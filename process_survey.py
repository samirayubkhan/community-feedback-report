#!/usr/bin/env python3
"""
ALX Community Feedback Survey Data Processor
Processes CSV survey data and creates categorized analysis for interactive HTML report.
"""

import pandas as pd
import json
import re
from collections import Counter, defaultdict
from typing import Dict, List, Any

def clean_text(text):
    """Clean and normalize text responses."""
    if pd.isna(text) or text == '':
        return ""
    return str(text).strip()

def analyze_sentiment(text):
    """
    Simple sentiment analysis based on keyword matching.
    Returns: 'positive', 'negative', or 'neutral'
    """
    if not text:
        return 'neutral'
    
    text_lower = text.lower()
    
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
        'annoying', 'difficult', 'hard', 'confusing', 'slow', 'laggy', 'broken', 'issue', 'problem',
        'bug', 'error', 'fail', 'failure', 'crash', 'freeze', 'stuck', 'impossible', 'useless',
        'waste', 'boring', 'unhappy', 'dissatisfied', 'concerned', 'worry', 'unfortunately', 'sadly'
    ]
    
    # Improvement/request words (usually neutral to positive)
    improvement_words = [
        'improve', 'better', 'enhance', 'upgrade', 'suggest', 'recommend', 'would like', 'hope',
        'wish', 'could', 'should', 'need', 'want', 'feature', 'add', 'include', 'provide'
    ]
    
    # Count occurrences
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    improvement_count = sum(1 for word in improvement_words if word in text_lower)
    
    # Determine sentiment
    if positive_count > negative_count and positive_count > 0:
        return 'positive'
    elif negative_count > positive_count and negative_count > 0:
        return 'negative'
    elif improvement_count > 0:
        return 'neutral'  # Suggestions/improvements are neutral
    else:
        return 'neutral'

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
    """Main function to process the survey data."""
    print("Loading survey data...")
    df = pd.read_csv(csv_file_path)
    
    # Clean column names
    df.columns = df.columns.str.strip()
    
    print(f"Total responses: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    
    # Find actual column names (handling potential trailing spaces)
    country_col = [col for col in df.columns if 'What country are you based in' in col][0]
    comm_pref_col = [col for col in df.columns if 'What is your preferred way to receive updates' in col][0]
    circle_rating_col = [col for col in df.columns if 'How would you rate you experience of Circle' in col][0]
    circle_feedback_col = [col for col in df.columns if 'Please share your reasoning behind your rating for Circle' in col][0]
    goals_col = [col for col in df.columns if 'What are the top 1-3 things you hope to gain' in col][0]
    events_col = [col for col in df.columns if 'To help us plan, what types of events' in col][0]
    content_col = [col for col in df.columns if 'What kind of content / articles / resources' in col][0]
    interest_col = [col for col in df.columns if 'If we were to create interest-based groups' in col][0]
    contribution_col = [col for col in df.columns if 'How would you be interested in contributing' in col][0]
    involve_col = [col for col in df.columns if 'Would you like us to inform you with specific ways' in col][0]
    suggestions_col = [col for col in df.columns if 'Do you have any other comments, questions or suggestion' in col][0]
    
    # Basic statistics
    stats = {
        'total_responses': len(df),
        'countries': df[country_col].value_counts().head(10).to_dict(),
        'communication_preferences': df[comm_pref_col].value_counts().to_dict(),
        'circle_ratings': df[circle_rating_col].value_counts().sort_index().to_dict()
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
    print("Categorizing text responses...")
    
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
            'countries_count': len([c for c in stats['countries'].keys() if c and str(c).strip()]),
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

if __name__ == "__main__":
    csv_file = "Online_community_feedback.csv"
    
    try:
        data = process_survey_data(csv_file)
        
        # Save processed data as JSON
        with open('survey_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print("\nProcessing complete!")
        print(f"Total responses processed: {data['stats']['total_responses']}")
        print(f"Countries represented: {data['stats']['countries_count']}")
        print(f"Average Circle rating: {data['stats']['avg_circle_rating']}")
        print(f"Want to contribute: {data['stats']['contribution_percentage']}%")
        
        print(f"\nData saved to 'survey_data.json'")
        
    except Exception as e:
        print(f"Error processing survey data: {e}")
        import traceback
        traceback.print_exc()