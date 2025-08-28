from ai.hf_client import hf_client
from bs4 import BeautifulSoup
import re
import asyncio
import aiohttp
from typing import Dict, List, Optional
import logging
from config.settings import settings

class SmartScraper:
    def __init__(self):
        self.extraction_questions = [
            "What is the event name?",
            "When is the event date?",
            "Where is the venue?",
            "What is the ticket price?",
            "Who are the performers or artists?",
            "What is the event description?",
            "What type of event is this?"
        ]
    
    async def extract_event_info_ai(self, html_content: str, url: str = "") -> Dict:
        """Extract structured event information using HuggingFace models"""
        
        # Clean HTML and extract text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        
        # Get clean text
        text_content = soup.get_text(separator=' ', strip=True)
        
        # Limit context length for AI processing
        max_length = settings.MAX_CONTEXT_LENGTH
        if len(text_content) > max_length:
            # Try to keep the most relevant parts
            text_content = self._extract_relevant_content(text_content, max_length)
        
        # Extract information using question-answering
        extracted_info = await hf_client.extract_info_qa(text_content, self.extraction_questions)
        
        # Post-process and structure the data
        structured_data = await self._structure_extracted_data(extracted_info, text_content, url)
        
        return structured_data
    
    async def batch_extract_from_urls(self, urls: List[str]) -> List[Dict]:
        """Extract festival data from multiple URLs concurrently"""
        
        semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)
        
        async def extract_single_url(url: str) -> Dict:
            async with semaphore:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=settings.REQUEST_TIMEOUT) as response:
                            if response.status == 200:
                                html_content = await response.text()
                                return await self.extract_event_info_ai(html_content, url)
                except Exception as e:
                    logging.error(f"Failed to extract from {url}: {e}")
                    return {}
        
        # Process all URLs concurrently
        tasks = [extract_single_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out failed extractions
        valid_results = [
            result for result in results 
            if isinstance(result, dict) and result.get('name')
        ]
        
        return valid_results
    
    async def smart_selector_detection(self, html_content: str) -> Dict[str, str]:
        """Use pattern matching to detect likely CSS selectors for event data"""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        selectors = {}
        
        # Common patterns for event information
        patterns = {
            'name': [
                {'tag': 'h1', 'class_contains': ['title', 'name', 'event']},
                {'tag': 'h2', 'class_contains': ['title', 'name', 'event']},
                {'class_contains': ['event-title', 'festival-name', 'title']}
            ],
            'date': [
                {'class_contains': ['date', 'time', 'when']},
                {'tag': 'time'},
                {'text_pattern': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'}
            ],
            'venue': [
                {'class_contains': ['venue', 'location', 'where', 'place']},
                {'text_pattern': r'\b\w+\s+(center|centre|hall|arena|stadium|park)\b'}
            ],
            'price': [
                {'class_contains': ['price', 'cost', 'ticket']},
                {'text_pattern': r'\$\d+(?:\.\d{2})?'}
            ]
        }
        
        for field, field_patterns in patterns.items():
            selector = self._find_best_selector(soup, field_patterns)
            if selector:
                selectors[field] = selector
        
        return selectors
    
    def _extract_relevant_content(self, text: str, max_length: int) -> str:
        """Extract the most relevant parts of content for AI processing"""
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        
        # Score sentences based on keywords
        event_keywords = [
            'festival', 'event', 'concert', 'show', 'performance', 'venue',
            'date', 'time', 'location', 'price', 'ticket', 'artist', 'performer'
        ]
        
        scored_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:  # Skip very short sentences
                continue
            
            score = sum(1 for keyword in event_keywords if keyword.lower() in sentence.lower())
            scored_sentences.append((sentence, score))
        
        # Sort by score and take top sentences that fit within limit
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        result = ""
        for sentence, score in scored_sentences:
            if len(result) + len(sentence) <= max_length:
                result += sentence + ". "
            else:
                break
        
        return result.strip()
    
    def _find_best_selector(self, soup: BeautifulSoup, patterns: List[Dict]) -> Optional[str]:
        """Find the best CSS selector based on patterns"""
        
        for pattern in patterns:
            elements = []
            
            if 'tag' in pattern and 'class_contains' in pattern:
                # Find elements by tag and class patterns
                tag_elements = soup.find_all(pattern['tag'])
                for element in tag_elements:
                    element_classes = element.get('class', [])
                    if any(keyword in ' '.join(element_classes).lower() 
                          for keyword in pattern['class_contains']):
                        elements.append(element)
            
            elif 'class_contains' in pattern:
                # Find elements by class patterns
                all_elements = soup.find_all(attrs={'class': True})
                for element in all_elements:
                    element_classes = element.get('class', [])
                    if any(keyword in ' '.join(element_classes).lower() 
                          for keyword in pattern['class_contains']):
                        elements.append(element)
            
            elif 'text_pattern' in pattern:
                # Find elements by text content pattern
                import re
                pattern_regex = re.compile(pattern['text_pattern'], re.IGNORECASE)
                all_elements = soup.find_all(string=pattern_regex)
                elements = [elem.parent for elem in all_elements if elem.parent]
            
            # Return selector for first matching element
            if elements:
                element = elements[0]
                return self._generate_css_selector(element)
        
        return None
    
    def _generate_css_selector(self, element) -> str:
        """Generate CSS selector for an element"""
        
        # Prefer ID selector
        if element.get('id'):
            return f"#{element['id']}"
        
        # Use class selector
        if element.get('class'):
            classes = element['class']
            return f".{'.'.join(classes)}"
        
        # Fallback to tag selector
        return element.name
    
    async def _structure_extracted_data(self, raw_data: Dict, full_text: str, url: str) -> Dict:
        """Structure and clean extracted data"""
        
        structured = {
            'name': '',
            'date': '',
            'venue': '',
            'city': '',
            'state': '',
            'price': None,
            'description': '',
            'artists': '',
            'url': url,
            'source_site': self._extract_domain(url),
            'category': ''
        }
        
        # Process each extracted field
        for field, value in raw_data.items():
            if not value or value.strip() == '':
                continue
            
            if field == 'name':
                structured['name'] = self._clean_name(value)
            elif field == 'date':
                structured['date'] = self._clean_date(value)
            elif field == 'venue':
                venue_info = self._parse_venue_location(value)
                structured.update(venue_info)
            elif field == 'price':
                structured['price'] = self._clean_price(value)
            elif field == 'description':
                structured['description'] = self._clean_description(value)
            elif field == 'artists':
                structured['artists'] = self._clean_artists(value)
            elif field == 'category':
                structured['category'] = self._clean_category(value)
        
        # Try to extract additional info from full text if fields are missing
        if not structured['description'] and len(full_text) > 100:
            structured['description'] = self._extract_description_from_text(full_text)
        
        return structured
    
    def _clean_name(self, name: str) -> str:
        """Clean and standardize event name"""
        if not name:
            return ""
        
        name = re.sub(r'\s+', ' ', name.strip())
        # Remove common prefixes
        name = re.sub(r'^(event[:\s]*|festival[:\s]*)', '', name, flags=re.IGNORECASE)
        
        return name
    
    def _clean_date(self, date_str: str) -> str:
        """Clean and parse date string"""
        if not date_str:
            return ""
        
        from dateutil import parser
        
        try:
            # Remove day of week if present
            date_str = re.sub(
                r'^(monday|tuesday|wednesday|thursday|friday|saturday|sunday)[,\s]*', 
                '', date_str, flags=re.IGNORECASE
            )
            
            parsed_date = parser.parse(date_str)
            return parsed_date.isoformat()
        except:
            return date_str
    
    def _parse_venue_location(self, venue_str: str) -> Dict:
        """Parse venue and location information"""
        
        result = {'venue': '', 'city': '', 'state': ''}
        
        if not venue_str:
            return result
        
        # Common pattern: "Venue Name, City, State"
        parts = [part.strip() for part in venue_str.split(',')]
        
        if len(parts) >= 1:
            result['venue'] = parts[0]
        if len(parts) >= 2:
            result['city'] = parts[1]
        if len(parts) >= 3:
            # Check if last part looks like a state
            last_part = parts[-1].strip()
            if len(last_part) <= 3 or any(state in last_part.lower() for state in 
                ['california', 'texas', 'florida', 'new york', 'illinois']):
                result['state'] = last_part
        
        return result
    
    def _clean_price(self, price_str: str) -> Optional[float]:
        """Extract and clean price information"""
        
        if not price_str:
            return None
        
        price_str = price_str.lower()
        
        # Handle free events
        if any(word in price_str for word in ['free', 'no charge', 'complimentary']):
            return 0.0
        
        # Extract numeric price
        price_match = re.search(r'\$?(\d+(?:\.\d{2})?)', price_str)
        if price_match:
            try:
                return float(price_match.group(1))
            except:
                pass
        
        return None
    
    def _clean_description(self, desc: str) -> str:
        """Clean description text"""
        
        if not desc:
            return ""
        
        # Clean whitespace
        desc = re.sub(r'\s+', ' ', desc.strip())
        
        # Remove common unwanted text
        desc = re.sub(r'(click here|read more|learn more)', '', desc, flags=re.IGNORECASE)
        
        # Limit length
        if len(desc) > 500:
            desc = desc[:500] + "..."
        
        return desc
    
    def _clean_artists(self, artists_str: str) -> str:
        """Clean artists/performers string"""
        
        if not artists_str:
            return ""
        
        # Clean and format
        artists_str = re.sub(r'\s+', ' ', artists_str.strip())
        
        # Split multiple artists and rejoin cleanly
        artists = [artist.strip() for artist in re.split(r'[,;&]', artists_str)]
        artists = [artist for artist in artists if len(artist) > 1]
        
        return ', '.join(artists[:5])  # Limit to 5 artists
    
    def _clean_category(self, category: str) -> str:
        """Clean category information"""
        
        if not category:
            return ""
        
        category = category.lower().strip()
        
        # Map to standard categories
        category_map = {
            'music': 'music_festival',
            'food': 'food_festival',
            'art': 'art_festival',
            'culture': 'cultural_festival',
            'tech': 'technology_conference'
        }
        
        for key, value in category_map.items():
            if key in category:
                return value
        
        return category.replace(' ', '_')
    
    def _extract_description_from_text(self, text: str) -> str:
        """Extract description from full text content"""
        
        # Look for descriptive paragraphs
        sentences = re.split(r'[.!?]+', text)
        
        # Find sentences that might be descriptions
        description_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if (len(sentence) > 50 and 
                any(word in sentence.lower() for word in 
                    ['festival', 'event', 'experience', 'enjoy', 'celebrate', 'featuring'])):
                description_sentences.append(sentence)
        
        if description_sentences:
            description = '. '.join(description_sentences[:3])  # Take first 3 sentences
            return description[:400] + "..." if len(description) > 400 else description
        
        return ""
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        
        import urllib.parse
        
        try:
            parsed = urllib.parse.urlparse(url)
            return parsed.netloc
        except:
            return ""

# Global instance
smart_scraper = SmartScraper()
