#!/usr/bin/env python3
"""
ALX City Community Feedback Survey Data Processor
Processes CSV survey data and creates categorized analysis for interactive HTML report.
"""

import pandas as pd
import json
import re
import difflib
import unicodedata
from datetime import datetime
from collections import Counter, defaultdict
from typing import Dict, List, Any

def clean_text(text):
    """Clean and normalize text responses."""
    if pd.isna(text) or text == '':
        return ""
    return str(text).strip()

def _normalize_location_string(raw: Any) -> str:
    """Normalize a free-text location to a simplified ASCII-ish lowercase string."""
    if pd.isna(raw) or raw == '':
        return ''
    text = str(raw).strip()
    # Replace unusual apostrophes/quotes with ASCII
    text = text.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    # Collapse consecutive whitespace
    text = re.sub(r"\s+", ' ', text)
    # Lowercase
    text = text.lower()
    # Strip emoji and symbols by allowing letters, spaces, commas, apostrophes, hyphens
    text = re.sub(r"[^a-z\s,'\-]", '', text)
    # Normalize accents for matching (we will restore canonical country names later)
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    # Collapse spaces again after removals
    text = re.sub(r"\s+", ' ', text).strip()
    return text

KNOWN_COUNTRIES = [
    'Algeria','Angola','Benin','Botswana','Burkina Faso','Burundi','Cabo Verde','Cameroon','Central African Republic',
    'Chad','Comoros','Congo','Democratic Republic of Congo','Côte d\'Ivoire','Djibouti','Egypt','Equatorial Guinea','Eritrea',
    'Eswatini','Ethiopia','Gabon','Gambia','Ghana','Guinea','Guinea-Bissau','Kenya','Lesotho','Liberia','Libya','Madagascar',
    'Malawi','Mali','Mauritania','Mauritius','Morocco','Mozambique','Namibia','Niger','Nigeria','Rwanda','Sao Tome and Principe',
    'Senegal','Seychelles','Sierra Leone','Somalia','South Africa','South Sudan','Sudan','Tanzania','Togo','Tunisia','Uganda',
    'Zambia','Zimbabwe',
    # Non-African commonly appearing
    'United States','United Kingdom','Canada','Germany','France','Saudi Arabia','United Arab Emirates','Brazil','Vietnam','Hungary','Belgium','South Korea','Turkey','Türkiye'
]

# Map common city/region terms to countries
CITY_TO_COUNTRY = {
    # Nigeria
    'lagos': 'Nigeria', 'abuja': 'Nigeria', 'ogun': 'Nigeria', 'ogun state': 'Nigeria', 'imo': 'Nigeria', 'imo state': 'Nigeria',
    # Kenya
    'nairobi': 'Kenya', 'nairobi metropolitan area': 'Kenya', 'mombasa': 'Kenya', 'kericho': 'Kenya',
    # Ghana
    'accra': 'Ghana', 'kumasi': 'Ghana',
    # South Africa
    'cape town': 'South Africa', 'johannesburg': 'South Africa', 'durban': 'South Africa', 'pretoria': 'South Africa',
    # Rwanda
    'kigali': 'Rwanda',
    # Egypt
    'cairo': 'Egypt', 'alexandria': 'Egypt',
    # Ethiopia
    'addis ababa': 'Ethiopia',
    # Morocco
    'casablanca': 'Morocco', 'rabat': 'Morocco',
    # Uganda
    'kampala': 'Uganda',
    # Zambia
    'lusaka': 'Zambia',
    # Zimbabwe
    'harare': 'Zimbabwe', 'bulawayo': 'Zimbabwe',
    # Botswana
    'gaborone': 'Botswana',
    # Namibia
    'windhoek': 'Namibia',
    # Cote d'Ivoire
    'abidjan': "Côte d'Ivoire", 'yamoussoukro': "Côte d'Ivoire",
    # DRC
    'kinshasa': 'Democratic Republic of Congo', 'lubumbashi': 'Democratic Republic of Congo',
    # Tunisia
    'tunis': 'Tunisia',
    # Saudi / UAE
    'riyadh': 'Saudi Arabia', 'jeddah': 'Saudi Arabia', 'dubai': 'United Arab Emirates', 'abu dhabi': 'United Arab Emirates',
    # Others
    'victoria': 'Seychelles', 'antananarivo': 'Madagascar', 'porto-novo': 'Benin', 'porto novo': 'Benin', 'cotonou': 'Benin',
    'bissau': 'Guinea-Bissau', 'bangui': 'Central African Republic', 'monrovia': 'Liberia', 'freetown': 'Sierra Leone',
    'lilongwe': 'Malawi', 'blantyre': 'Malawi', 'dodoma': 'Tanzania', 'dar es salaam': 'Tanzania', 'yaounde': 'Cameroon', 'yaoundé': 'Cameroon', 'douala': 'Cameroon', 'nouakchott': 'Mauritania', 'mbabane': 'Eswatini', 'maseru': 'Lesotho'
}

CANONICAL_NAME_FIXES = {
    'cote divoire': "Côte d'Ivoire",
    'cote d ivoire': "Côte d'Ivoire",
    'cote d\'ivoire': "Côte d'Ivoire",
    'south  africa': 'South Africa',
    'uae': 'United Arab Emirates',
    'uk': 'United Kingdom',
    'usa': 'United States',
    'us': 'United States',
    'britain': 'United Kingdom',
    'england': 'United Kingdom',
    'sa': 'South Africa',
    'rsa': 'South Africa',
    'ken': 'Kenya',
    'keny': 'Kenya',
    'kennya': 'Kenya',
    'ghan': 'Ghana',
    'egy': 'Egypt',
    'ethi': 'Ethiopia',
    'rwan': 'Rwanda',
    'moro': 'Morocco',
    'maroc': 'Morocco',
    'marocco': 'Morocco',
    'zimb': 'Zimbabwe',
    'tanz': 'Tanzania',
    'zamb': 'Zambia',
    'camer': 'Cameroon',
    'nig': 'Nigeria'
}

NON_COUNTRY_BLACKLIST_EXACT = {
    'tourism and hospitality', 'country', 'marketing'
}
NON_COUNTRY_BLACKLIST_SUBSTR = {
    'gmail', 'yahoo', 'outlook', 'hotmail', 'mail', 'gmailcom', 'yahoocom', 'email', 'com', 'http', 'https'
}

def _best_country_match(text_normalized: str) -> str:
    """Try to match a normalized string to a canonical country using heuristics and fuzzy matching."""
    if not text_normalized:
        return ''

    # If contains comma, take the last part (often the country)
    if ',' in text_normalized:
        parts = [p.strip() for p in text_normalized.split(',') if p.strip()]
        if len(parts) >= 2:
            text_normalized = parts[-1]

    # Direct city mapping
    if text_normalized in CITY_TO_COUNTRY:
        return CITY_TO_COUNTRY[text_normalized]

    # Canonical short/alias fixes
    if text_normalized in CANONICAL_NAME_FIXES:
        return CANONICAL_NAME_FIXES[text_normalized]

    # Special-case common shadowing: ensure 'Nigeria' wins over 'Niger'
    if re.search(r"\bnigeria\b", text_normalized):
        return 'Nigeria'

    # Direct includes of country names using word boundaries, prefer longer country names first
    for country in sorted(KNOWN_COUNTRIES, key=lambda c: -len(c)):
        pattern = r"\b" + re.escape(country.lower()) + r"\b"
        if re.search(pattern, text_normalized):
            return country

    # Try fuzzy matching to country list (threshold tuned for short typos like "Keny", "Nig")
    candidates = difflib.get_close_matches(text_normalized.title(), KNOWN_COUNTRIES, n=1, cutoff=0.8)
    if candidates:
        return candidates[0]

    # If the text equals a known city term (not exact key), try contains-based city mapping
    for city_key, mapped_country in CITY_TO_COUNTRY.items():
        if city_key in text_normalized:
            return mapped_country

    return ''

def clean_country_name(country):
    """Clean and normalize country names, handling city-country combinations."""
    if pd.isna(country) or country == '':
        return ""
    
    # Convert to string and clean
    country_clean = str(country).strip()
    country_lower = country_clean.lower()
    
    # Handle city, country patterns (e.g., "Lagos, Nigeria", "Cape Town, South Africa")
    if ',' in country_clean:
        parts = [part.strip() for part in country_clean.split(',')]
        # Take the last part as it's usually the country
        if len(parts) >= 2:
            country_clean = parts[-1].strip()
            country_lower = country_clean.lower()
    
    # Handle common country name patterns in the location
    # Check for country names mentioned anywhere in the text
    if 'nigeria' in country_lower:
        return 'Nigeria'
    elif 'south africa' in country_lower or country_lower in ['sa', 'rsa', 'sou', 'south', 'cape town', 'johannesburg', 'durban', 'pretoria']:
        return 'South Africa'
    elif 'kenya' in country_lower or country_lower in ['nairobi', 'mombasa', 'ken']:
        return 'Kenya'
    elif 'ghana' in country_lower or country_lower in ['accra', 'kumasi', 'ghan']:
        return 'Ghana'
    elif 'egypt' in country_lower or country_lower in ['cairo', 'alexandria', 'egy']:
        return 'Egypt'
    elif 'ethiopia' in country_lower or country_lower in ['addis ababa', 'eth', 'ethi']:
        return 'Ethiopia'
    elif 'rwanda' in country_lower or country_lower in ['kigali', 'rwan']:
        return 'Rwanda'
    elif 'morocco' in country_lower or country_lower in ['casablanca', 'rabat', 'maroc', 'moro']:
        return 'Morocco'
    elif 'uganda' in country_lower or country_lower in ['kampala', 'ugan']:
        return 'Uganda'
    elif 'zimbabwe' in country_lower or country_lower in ['harare', 'bulawayo', 'zimb']:
        return 'Zimbabwe'
    elif 'malawi' in country_lower or country_lower in ['lilongwe', 'blantyre', 'mala']:
        return 'Malawi'
    elif 'tanzania' in country_lower or country_lower in ['dar es salaam', 'dodoma', 'tanz']:
        return 'Tanzania'
    elif 'zambia' in country_lower or country_lower in ['lusaka', 'ndola', 'zamb']:
        return 'Zambia'
    elif 'cameroon' in country_lower or country_lower in ['yaoundé', 'douala', 'camer']:
        return 'Cameroon'
    elif 'sudan' in country_lower or country_lower in ['khartoum', 'suda']:
        return 'Sudan'
    elif 'angola' in country_lower or country_lower in ['luanda', 'ango']:
        return 'Angola'
    elif 'tunisia' in country_lower or country_lower in ['tunis', 'tuni']:
        return 'Tunisia'
    elif 'algeria' in country_lower or country_lower in ['algiers', 'alge']:
        return 'Algeria'
    elif 'senegal' in country_lower or country_lower in ['dakar', 'sene']:
        return 'Senegal'
    elif 'ivory coast' in country_lower or 'côte d\'ivoire' in country_lower or country_lower in ['abidjan', 'yamoussoukro']:
        return 'Côte d\'Ivoire'
    elif 'democratic republic of congo' in country_lower or 'drc' in country_lower or country_lower in ['kinshasa', 'lubumbashi']:
        return 'Democratic Republic of Congo'
    elif 'burkina faso' in country_lower or country_lower in ['ouagadougou', 'burk']:
        return 'Burkina Faso'
    elif 'mali' in country_lower or country_lower in ['bamako']:
        return 'Mali'
    elif 'niger' in country_lower and 'nigeria' not in country_lower:
        return 'Niger'
    elif 'chad' in country_lower or country_lower in ['n\'djamena']:
        return 'Chad'
    elif 'liberia' in country_lower or country_lower in ['monrovia', 'libe']:
        return 'Liberia'
    elif 'sierra leone' in country_lower or country_lower in ['freetown', 'sier']:
        return 'Sierra Leone'
    elif 'guinea' in country_lower and 'equatorial' not in country_lower:
        return 'Guinea'
    elif 'togo' in country_lower or country_lower in ['lomé']:
        return 'Togo'
    elif 'benin' in country_lower or country_lower in ['porto-novo', 'cotonou']:
        return 'Benin'
    elif 'gambia' in country_lower or country_lower in ['banjul']:
        return 'Gambia'
    elif 'guinea-bissau' in country_lower or country_lower in ['bissau']:
        return 'Guinea-Bissau'
    elif 'equatorial guinea' in country_lower or country_lower in ['malabo']:
        return 'Equatorial Guinea'
    elif 'gabon' in country_lower or country_lower in ['libreville']:
        return 'Gabon'
    elif 'congo' in country_lower and 'democratic' not in country_lower:
        return 'Congo'
    elif 'central african republic' in country_lower or country_lower in ['bangui']:
        return 'Central African Republic'
    elif 'mauritania' in country_lower or country_lower in ['nouakchott']:
        return 'Mauritania'
    elif 'botswana' in country_lower or country_lower in ['gaborone']:
        return 'Botswana'
    elif 'namibia' in country_lower or country_lower in ['windhoek']:
        return 'Namibia'
    elif 'swaziland' in country_lower or 'eswatini' in country_lower or country_lower in ['mbabane']:
        return 'Eswatini'
    elif 'lesotho' in country_lower or country_lower in ['maseru']:
        return 'Lesotho'
    elif 'mauritius' in country_lower or country_lower in ['port louis']:
        return 'Mauritius'
    elif 'seychelles' in country_lower or country_lower in ['victoria']:
        return 'Seychelles'
    elif 'madagascar' in country_lower or country_lower in ['antananarivo']:
        return 'Madagascar'
    elif 'comoros' in country_lower or country_lower in ['moroni']:
        return 'Comoros'
    
    # Handle non-African countries that might appear
    elif 'united states' in country_lower or country_lower in ['usa', 'us', 'america']:
        return 'United States'
    elif 'united kingdom' in country_lower or country_lower in ['uk', 'britain', 'england']:
        return 'United Kingdom'
    elif 'canada' in country_lower:
        return 'Canada'
    elif 'germany' in country_lower:
        return 'Germany'
    elif 'france' in country_lower:
        return 'France'
    elif 'united arab emirates' in country_lower or country_lower in ['uae', 'dubai', 'abu dhabi']:
        return 'United Arab Emirates'
    elif 'saudi arabia' in country_lower or country_lower in ['riyadh', 'jeddah']:
        return 'Saudi Arabia'
    
    # Clean up the country name for title case
    country_clean = country_clean.title()
    
    # If it's clearly not a country (too long, contains non-country terms), return empty
    non_country_indicators = ['job', 'career', 'skill', 'network', 'email', '@', 'opportunity', 'marketing', 'thanks']
    if len(country_clean) > 30 or any(indicator in country_lower for indicator in non_country_indicators):
        return ""
    
    return country_clean

# Override with improved country cleaner from the main processor
def clean_country_name(country):
    """Clean and normalize country names, handling city-country combinations and common typos."""
    if pd.isna(country) or country == '':
        return ''

    normalized = _normalize_location_string(country)
    if not normalized:
        return ''

    if normalized in NON_COUNTRY_BLACKLIST_EXACT:
        return ''
    if any(bad in normalized for bad in NON_COUNTRY_BLACKLIST_SUBSTR):
        return ''

    best = _best_country_match(normalized)
    if best:
        return best

    tokens = normalized.split()
    if 1 <= len(tokens) <= 3 and len(normalized) <= 30:
        fallback = ' '.join(tokens).title()
        if not any(bad in normalized for bad in ['@', 'job', 'career', 'skill', 'network', 'opportunity', 'thanks', 'gmail', 'mail']):
            return fallback
    return ''

def analyze_sentiment(text):
    """
    Heuristic sentiment analysis with negation handling and common phrases.
    Returns: 'positive', 'negative', or 'neutral'
    """
    if not text:
        return 'neutral'

    text_lower = str(text).lower()

    # Positive indicators
    positive_words = [
        'love', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'awesome', 'good', 'nice',
        'helpful', 'useful', 'valuable', 'appreciate', 'thank', 'grateful', 'enjoy', 'happy',
        'satisfied', 'perfect', 'outstanding', 'impressive', 'beneficial', 'effective', 'successful',
        'easy', 'smooth', 'clear', 'convenient', 'accessible', 'friendly', 'supportive', 'inspiring'
    ]

    # Negative indicators
    negative_words = [
        'hate', 'terrible', 'awful', 'horrible', 'bad', 'poor', 'disappointing', 'frustrated',
        'annoying', 'difficult', 'hard', 'confusing', 'slow', 'lag', 'laggy', 'broken', 'issue', 'problem',
        'bug', 'error', 'fail', 'failure', 'crash', 'crashing', 'freeze', 'freezes', 'freezing', 'stuck',
        'impossible', 'useless', 'waste', 'boring', 'unhappy', 'dissatisfied', 'concerned', 'worry', 'unfortunately', 'sadly',
        'unresponsive'
    ]

    # Improvement/request words (usually neutral to positive)
    improvement_words = [
        'improve', 'better', 'enhance', 'upgrade', 'suggest', 'recommend', 'would like', 'hope',
        'wish', 'could', 'should', 'need', 'want', 'feature', 'add', 'include', 'provide'
    ]

    # Negation or problem phrase patterns that indicate negative sentiment
    negative_patterns = [
        'not good', 'not great', 'not helpful', 'not useful', 'no value', 'no good',
        "don't like", 'do not like', "doesn't work", "doesnt work", "can't", 'cant ', 'cannot ',
        'hard to', 'difficult to', 'too slow', 'very slow', 'so slow', 'keeps crashing', 'keeps crushing'
    ]

    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    improvement_count = sum(1 for word in improvement_words if word in text_lower)
    negative_count += sum(1 for pat in negative_patterns if pat in text_lower)

    # Mixed signal handling
    if negative_count > 0 and positive_count > 0:
        if negative_count - positive_count >= 1:
            return 'negative'
        if positive_count - negative_count >= 1:
            return 'positive'
        return 'neutral'

    if negative_count > 0:
        return 'negative'
    if positive_count > 0:
        return 'positive'
    if improvement_count > 0:
        return 'neutral'
    return 'neutral'

def _parse_timestamp(ts_val: Any) -> datetime:
    if pd.isna(ts_val):
        return datetime.min
    s = str(ts_val).strip()
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    try:
        return pd.to_datetime(s, errors='coerce') or datetime.min
    except Exception:
        return datetime.min

def deduplicate_by_email(df: pd.DataFrame) -> pd.DataFrame:
    """Deduplicate responses by email, keeping the latest Timestamp per email (case-insensitive)."""
    email_cols = [col for col in df.columns if 'email' in col.lower()]
    ts_cols = [col for col in df.columns if 'timestamp' in col.lower()]
    if not email_cols or not ts_cols:
        return df

    email_col = email_cols[0]
    ts_col = ts_cols[0]

    df['_email_norm'] = df[email_col].astype(str).str.strip().str.lower()
    df['_ts_parsed'] = df[ts_col].apply(_parse_timestamp)

    with_email = df[df['_email_norm'].fillna('') != '']
    without_email = df[df['_email_norm'].fillna('') == '']

    if with_email.empty:
        return df.drop(columns=['_email_norm', '_ts_parsed'], errors='ignore')

    idx = with_email.groupby('_email_norm')['_ts_parsed'].idxmax()
    deduped = with_email.loc[idx]

    result = pd.concat([deduped, without_email], ignore_index=True)
    return result.drop(columns=['_email_norm', '_ts_parsed'], errors='ignore')

def _require_column(df: pd.DataFrame, needle: str) -> str:
    matches = [col for col in df.columns if needle in col]
    if not matches:
        raise ValueError(f"Required column containing '{needle}' not found. Available: {list(df.columns)}")
    return matches[0]

def _format_circle_ratings(series: pd.Series) -> Dict[str, int]:
    counts = series.value_counts().sort_index()
    formatted: Dict[str, int] = {}
    for k, v in counts.items():
        try:
            key = f"{float(k):.1f}"
        except Exception:
            key = str(k)
        formatted[key] = int(v)
    return formatted

def categorize_community_goals(responses):
    """Categorize responses about what members hope to gain."""
    categories = {
        'Career Development & Job Opportunities': [],
        'Networking & Community Building': [],
        'Skill Development & Learning': [],
        'Business & Entrepreneurship': [],
        'Mentorship & Guidance': [],
        'Other': []
    }
    
    career_keywords = ['job', 'career', 'opportunity', 'employment', 'professional development', 'interview', 'resume', 'hire', 'position']
    network_keywords = ['network', 'connect', 'community', 'friendship', 'relationship', 'collaborate', 'partnership']
    skill_keywords = ['skill', 'learn', 'knowledge', 'education', 'training', 'course', 'expertise', 'development', 'upskill']
    business_keywords = ['business', 'startup', 'entrepreneur', 'fund', 'investment', 'scale', 'venture', 'cofounder']
    mentor_keywords = ['mentor', 'guidance', 'advice', 'support', 'help', 'coaching']
    
    for response in responses:
        response_clean = clean_text(response).lower()
        if not response_clean:
            continue
        
        # Add sentiment analysis
        sentiment = analyze_sentiment(response)
        response_with_sentiment = {'text': response, 'sentiment': sentiment}
            
        categorized = False
        
        if any(keyword in response_clean for keyword in career_keywords):
            categories['Career Development & Job Opportunities'].append(response_with_sentiment)
            categorized = True
        elif any(keyword in response_clean for keyword in network_keywords):
            categories['Networking & Community Building'].append(response_with_sentiment)
            categorized = True
        elif any(keyword in response_clean for keyword in skill_keywords):
            categories['Skill Development & Learning'].append(response_with_sentiment)
            categorized = True
        elif any(keyword in response_clean for keyword in business_keywords):
            categories['Business & Entrepreneurship'].append(response_with_sentiment)
            categorized = True
        elif any(keyword in response_clean for keyword in mentor_keywords):
            categories['Mentorship & Guidance'].append(response_with_sentiment)
            categorized = True
            
        if not categorized:
            categories['Other'].append(response_with_sentiment)
    
    return categories

def categorize_circle_feedback(responses):
    """Categorize Circle platform feedback."""
    categories = {
        'Positive User Experience': [],
        'Performance Issues': [],
        'Content Organization': [],
        'Navigation & Usability': [],
        'Feature Requests': [],
        'Other': []
    }
    
    positive_keywords = ['love', 'great', 'good', 'easy', 'nice', 'excellent', 'wonderful', 'amazing', 'helpful', 'useful']
    performance_keywords = ['slow', 'load', 'lag', 'freeze', 'crash', 'speed', 'fast', 'performance']
    content_keywords = ['content', 'post', 'organize', 'structure', 'format', 'layout']
    navigation_keywords = ['navigate', 'find', 'search', 'menu', 'interface', 'design', 'user experience']
    feature_keywords = ['feature', 'add', 'need', 'want', 'suggest', 'improve', 'enhancement']
    
    for response in responses:
        response_clean = clean_text(response).lower()
        if not response_clean:
            continue
        
        # Add sentiment analysis
        sentiment = analyze_sentiment(response)
        response_with_sentiment = {'text': response, 'sentiment': sentiment}
            
        categorized = False
        
        if any(keyword in response_clean for keyword in positive_keywords):
            categories['Positive User Experience'].append(response_with_sentiment)
            categorized = True
        elif any(keyword in response_clean for keyword in performance_keywords):
            categories['Performance Issues'].append(response_with_sentiment)
            categorized = True
        elif any(keyword in response_clean for keyword in content_keywords):
            categories['Content Organization'].append(response_with_sentiment)
            categorized = True
        elif any(keyword in response_clean for keyword in navigation_keywords):
            categories['Navigation & Usability'].append(response_with_sentiment)
            categorized = True
        elif any(keyword in response_clean for keyword in feature_keywords):
            categories['Feature Requests'].append(response_with_sentiment)
            categorized = True
            
        if not categorized:
            categories['Other'].append(response_with_sentiment)
    
    return categories

def categorize_content_preferences(responses):
    """Categorize what kind of content members want."""
    categories = {
        'Career Tips & Opportunities': [],
        'Technical Skills & AI Content': [],
        'Industry Trends & Leadership': [],
        'Personal Development': [],
        'Educational Resources': [],
        'Other': []
    }
    
    career_keywords = ['career', 'job', 'opportunity', 'interview', 'resume', 'professional']
    tech_keywords = ['ai', 'tech', 'coding', 'programming', 'development', 'software', 'web3', 'data', 'analytics']
    trends_keywords = ['trend', 'industry', 'leader', 'leadership', 'business', 'innovation']
    personal_keywords = ['personal', 'motivation', 'inspiration', 'growth', 'mindset']
    education_keywords = ['education', 'learn', 'tutorial', 'guide', 'course', 'training']
    
    for response in responses:
        response_clean = clean_text(response).lower()
        if not response_clean:
            continue
        
        # Add sentiment analysis
        sentiment = analyze_sentiment(response)
        response_with_sentiment = {'text': response, 'sentiment': sentiment}
            
        categorized = False
        
        if any(keyword in response_clean for keyword in career_keywords):
            categories['Career Tips & Opportunities'].append(response_with_sentiment)
            categorized = True
        elif any(keyword in response_clean for keyword in tech_keywords):
            categories['Technical Skills & AI Content'].append(response_with_sentiment)
            categorized = True
        elif any(keyword in response_clean for keyword in trends_keywords):
            categories['Industry Trends & Leadership'].append(response_with_sentiment)
            categorized = True
        elif any(keyword in response_clean for keyword in personal_keywords):
            categories['Personal Development'].append(response_with_sentiment)
            categorized = True
        elif any(keyword in response_clean for keyword in education_keywords):
            categories['Educational Resources'].append(response_with_sentiment)
            categorized = True
            
        if not categorized:
            categories['Other'].append(response_with_sentiment)
    
    return categories

def categorize_interest_groups(responses):
    """Categorize interest group preferences."""
    categories = {
        'Developer & Tech Groups': [],
        'Data Science & Analytics': [],
        'AI & Machine Learning': [],
        'Business & Finance': [],
        'Design & Creative': [],
        'Other': []
    }
    
    dev_keywords = ['developer', 'programming', 'coding', 'software', 'web', 'mobile', 'frontend', 'backend']
    data_keywords = ['data', 'analytics', 'science', 'statistics', 'analysis']
    ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning']
    business_keywords = ['business', 'finance', 'accounting', 'investment', 'marketing', 'sales']
    design_keywords = ['design', 'ui', 'ux', 'creative', 'art', 'graphics']
    
    for response in responses:
        response_clean = clean_text(response).lower()
        if not response_clean:
            continue
        
        # Add sentiment analysis
        sentiment = analyze_sentiment(response)
        response_with_sentiment = {'text': response, 'sentiment': sentiment}
            
        categorized = False
        
        if any(keyword in response_clean for keyword in dev_keywords):
            categories['Developer & Tech Groups'].append(response_with_sentiment)
            categorized = True
        elif any(keyword in response_clean for keyword in data_keywords):
            categories['Data Science & Analytics'].append(response_with_sentiment)
            categorized = True
        elif any(keyword in response_clean for keyword in ai_keywords):
            categories['AI & Machine Learning'].append(response_with_sentiment)
            categorized = True
        elif any(keyword in response_clean for keyword in business_keywords):
            categories['Business & Finance'].append(response_with_sentiment)
            categorized = True
        elif any(keyword in response_clean for keyword in design_keywords):
            categories['Design & Creative'].append(response_with_sentiment)
            categorized = True
            
        if not categorized:
            categories['Other'].append(response_with_sentiment)
    
    return categories

def categorize_suggestions(responses):
    """Categorize suggestions and comments."""
    categories = {
        'Platform & Technical Improvements': [],
        'Community Structure & Organization': [],
        'Opportunities & Accessibility': [],
        'Mentorship & Support': [],
        'Content & Resources': [],
        'Other': []
    }
    
    platform_keywords = ['platform', 'app', 'website', 'technical', 'slow', 'bug', 'fix', 'improve', 'interface']
    community_keywords = ['community', 'group', 'organize', 'structure', 'channel', 'discussion']
    opportunity_keywords = ['opportunity', 'scholarship', 'job', 'access', 'available', 'fair', 'equal']
    mentorship_keywords = ['mentor', 'support', 'help', 'guidance', 'coaching', 'advice']
    content_keywords = ['content', 'resource', 'material', 'course', 'learning']
    
    for response in responses:
        response_clean = clean_text(response).lower()
        if not response_clean:
            continue
        
        # Add sentiment analysis
        sentiment = analyze_sentiment(response)
        response_with_sentiment = {'text': response, 'sentiment': sentiment}
            
        categorized = False
        
        if any(keyword in response_clean for keyword in platform_keywords):
            categories['Platform & Technical Improvements'].append(response_with_sentiment)
            categorized = True
        elif any(keyword in response_clean for keyword in community_keywords):
            categories['Community Structure & Organization'].append(response_with_sentiment)
            categorized = True
        elif any(keyword in response_clean for keyword in opportunity_keywords):
            categories['Opportunities & Accessibility'].append(response_with_sentiment)
            categorized = True
        elif any(keyword in response_clean for keyword in mentorship_keywords):
            categories['Mentorship & Support'].append(response_with_sentiment)
            categorized = True
        elif any(keyword in response_clean for keyword in content_keywords):
            categories['Content & Resources'].append(response_with_sentiment)
            categorized = True
            
        if not categorized:
            categories['Other'].append(response_with_sentiment)
    
    return categories

def process_survey_data(csv_file_path):
    """Main function to process the city survey data."""
    print("Loading city survey data...")
    # Use proper CSV parsing with quote handling
    df = pd.read_csv(csv_file_path, quotechar='"', skipinitialspace=True)
    
    # Clean column names
    df.columns = df.columns.str.strip()

    # Deduplicate by email keeping latest timestamp when present
    df = deduplicate_by_email(df)
    
    print(f"Total city responses: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    
    # Find actual column names (robust substring search)
    country_col = _require_column(df, 'What country are you based in')
    comm_pref_col = _require_column(df, 'What is your preferred way to receive updates')
    circle_rating_col = _require_column(df, 'How would you rate you experience of Circle')
    circle_feedback_col = _require_column(df, 'Please share your reasoning behind your rating for Circle')
    goals_col = _require_column(df, 'What are the top 1-3 things you hope to gain')
    events_col = _require_column(df, 'To help us plan, what types of events')
    content_col = _require_column(df, 'What kind of content / articles / resources')
    interest_col = _require_column(df, 'If we were to create interest-based groups')
    contribution_col = _require_column(df, 'How would you be interested in contributing')
    involve_col = _require_column(df, 'Would you like us to inform you with specific ways')
    suggestions_col = _require_column(df, 'Do you have any other comments, questions or suggestion')
    
    # Clean and normalize country names
    print("Cleaning city survey country data...")
    df[country_col] = df[country_col].apply(clean_country_name)
    # Do NOT drop rows with missing country; bucket them as 'Unknown' for country stats
    country_series_for_stats = df[country_col].replace('', 'Unknown')
    
    # Basic statistics
    # Coerce circle rating to numeric for consistency prior to formatting
    df[circle_rating_col] = pd.to_numeric(df[circle_rating_col], errors='coerce')
    stats = {
        'total_responses': len(df),
        'countries': country_series_for_stats.value_counts().to_dict(),
        'communication_preferences': df[comm_pref_col].value_counts().to_dict(),
        'circle_ratings': _format_circle_ratings(df[circle_rating_col].dropna())
    }
    
    # Process value ratings for community aspects
    value_columns = [
        'How valuable do you find the following aspects of the ALX community? [Online Events (e.g., webinars, workshops)]',
        'How valuable do you find the following aspects of the ALX community? [In-person Events (e.g., meetups, networking sessions)]',
        'How valuable do you find the following aspects of the ALX community? [The community platform (Circle)]',
        'How valuable do you find the following aspects of the ALX community? [Networking opportunities with other members]',
        'How valuable do you find the following aspects of the ALX community? [Content and resources shared with community]'
    ]
    
    value_ratings = {}
    for col in value_columns:
        if col in df.columns:
            short_name = col.split('[')[1].split(']')[0]
            value_ratings[short_name] = df[col].value_counts().to_dict()
    
    # Process text responses
    print("Categorizing city text responses...")
    
    # Community goals
    goals_responses = df[goals_col].dropna().tolist()
    categorized_goals = categorize_community_goals(goals_responses)
    
    # Circle feedback
    circle_feedback = df[circle_feedback_col].dropna().tolist()
    categorized_circle = categorize_circle_feedback(circle_feedback)
    
    # Content preferences
    content_responses = df[content_col].dropna().tolist()
    categorized_content = categorize_content_preferences(content_responses)
    
    # Interest groups
    interest_responses = df[interest_col].dropna().tolist()
    categorized_interests = categorize_interest_groups(interest_responses)
    
    # Suggestions
    suggestions_responses = df[suggestions_col].dropna().tolist()
    categorized_suggestions = categorize_suggestions(suggestions_responses)
    
    # Event preferences
    event_responses = df[events_col].dropna().tolist()
    event_types = Counter()
    for response in event_responses:
        if pd.notna(response):
            # Count mentions of different event types
            response_lower = str(response).lower()
            if 'skill' in response_lower or 'workshop' in response_lower:
                event_types['Skill-building Workshops'] += 1
            if 'career' in response_lower or 'networking' in response_lower:
                event_types['Career Development'] += 1
            if 'q&a' in response_lower or 'expert' in response_lower:
                event_types['Expert Q&A'] += 1
            if 'meetup' in response_lower or 'local' in response_lower:
                event_types['Local Meetups'] += 1
            if 'social' in response_lower or 'hangout' in response_lower:
                event_types['Social Hangouts'] += 1
            if 'presentation' in response_lower or 'showcase' in response_lower:
                event_types['Presentations'] += 1
    
    # Contribution preferences
    contribution_responses = df[contribution_col].dropna().tolist()
    contribution_types = Counter()
    for response in contribution_responses:
        if pd.notna(response):
            response_lower = str(response).lower()
            if 'content' in response_lower or 'sharing' in response_lower or 'article' in response_lower:
                contribution_types['Content Sharing'] += 1
            if 'mentor' in response_lower:
                contribution_types['Mentoring'] += 1
            if 'host' in response_lower or 'event' in response_lower:
                contribution_types['Event Hosting'] += 1
            if 'moderat' in response_lower:
                contribution_types['Moderating'] += 1
            if 'not ready' in response_lower or 'attend' in response_lower:
                contribution_types['Not Ready Yet'] += 1
    
    # Calculate average Circle rating
    circle_ratings_numeric = df[circle_rating_col].dropna()
    avg_circle_rating = circle_ratings_numeric.mean() if len(circle_ratings_numeric) > 0 else 0
    
    # Calculate contribution interest percentage
    contribution_interest = df[involve_col].value_counts().to_dict()
    contribution_percentage = (contribution_interest.get('Yes', 0) / len(df) * 100) if len(df) > 0 else 0
    
    # Compile final data
    processed_data = {
        'stats': {
            'total_responses': stats['total_responses'],
            'countries_count': len(stats['countries']),  # Now showing actual clean country count
            'avg_circle_rating': round(avg_circle_rating, 1),
            'contribution_percentage': round(contribution_percentage)
        },
        'countries': stats['countries'],
        'communication_preferences': stats['communication_preferences'],
        'circle_ratings': stats['circle_ratings'],
        'value_ratings': value_ratings,
        'event_preferences': dict(event_types),
        'contribution_preferences': dict(contribution_types),
        'categorized_responses': {
            'community_goals': categorized_goals,
            'circle_feedback': categorized_circle,
            'content_preferences': categorized_content,
            'interest_groups': categorized_interests,
            'suggestions': categorized_suggestions
        }
    }
    
    return processed_data

def write_js(data: Dict[str, Any], output_js_path: str = 'city_survey_data.js') -> None:
    """Write processed city data as a JS constant used by the dashboard."""
    with open(output_js_path, 'w', encoding='utf-8') as f:
        f.write('const citySurveyData = ')
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write(';' + "\n")

if __name__ == "__main__":
    csv_file = "(City) ALX Community Feedback Form (Responses) - Form Responses 1 (1).csv"
    
    try:
        data = process_survey_data(csv_file)
        
        # Save processed data as JSON
        with open('city_survey_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Save as JS for the report
        write_js(data, 'city_survey_data.js')
        
        print("\nCity survey processing complete!")
        print(f"Total city responses processed: {data['stats']['total_responses']}")
        print(f"Countries represented: {data['stats']['countries_count']}")
        print(f"Average Circle rating: {data['stats']['avg_circle_rating']}")
        print(f"Want to contribute: {data['stats']['contribution_percentage']}%")
        
        print(f"\nCity data saved to 'city_survey_data.json' and 'city_survey_data.js'")
        
    except Exception as e:
        print(f"Error processing city survey data: {e}")
        import traceback
        traceback.print_exc()
