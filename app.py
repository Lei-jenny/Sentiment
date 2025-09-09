#!/usr/bin/env python3
"""
AI Hospitality Sentiment Dashboard Server (Vercel Compatible)
Serves the HTML dashboard and provides API endpoints for data
"""

import csv
import os
import json
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Global variables
reviews_data = []
last_updated = None

def load_real_data():
    """Load real data from CSV file"""
    reviews = []
    
    # For Vercel deployment, we'll use a static CSV file
    csv_file = 'data.csv'  # You'll upload this as a static file
    
    if os.path.exists(csv_file):
        try:
            # Try different encodings to handle various file formats
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            file_loaded = False
            
            for encoding in encodings:
                try:
                    temp_reviews = []
                    
                    with open(csv_file, 'r', encoding=encoding) as file:
                        reader = csv.DictReader(file)
                        file_reviews = 0
                        
                        # Get column names for processing
                        columns = reader.fieldnames
                        
                        for row in reader:
                            # Handle different column structures
                            hotel_name = row.get('hotel_name', '') or row.get('Hotel Name', '') or row.get('hotel', '')
                            city = row.get('city', '') or row.get('City', '') or row.get('location', '')
                            review_text = row.get('review_text', '') or row.get('Review Text', '') or row.get('review', '')
                            sentiment = row.get('sentiment', '') or row.get('Sentiment', '') or row.get('sentiment_score', '')
                            rating = row.get('rating', '') or row.get('Rating', '') or row.get('score', '')
                            date = row.get('date', '') or row.get('Date', '') or row.get('review_date', '')
                            categories = row.get('categories', '') or row.get('Categories', '') or row.get('category', '')
                            keywords = row.get('keywords', '') or row.get('Keywords', '') or row.get('keyword', '')
                            
                            # Skip empty rows
                            if not review_text or not hotel_name:
                                continue
                            
                            # Convert rating to float if possible
                            try:
                                rating_float = float(rating) if rating else 0.0
                            except (ValueError, TypeError):
                                rating_float = 0.0
                            
                            # Convert sentiment to float if possible
                            try:
                                sentiment_float = float(sentiment) if sentiment else 0.0
                            except (ValueError, TypeError):
                                sentiment_float = 0.0
                            
                            review = {
                                'hotel_name': hotel_name.strip(),
                                'city': city.strip(),
                                'review_text': review_text.strip(),
                                'sentiment': sentiment_float,
                                'rating': rating_float,
                                'date': date.strip(),
                                'categories': categories.strip(),
                                'keywords': keywords.strip()
                            }
                            
                            temp_reviews.append(review)
                            file_reviews += 1
                    
                    if temp_reviews:
                        reviews.extend(temp_reviews)
                        file_loaded = True
                        print(f"Loaded {file_reviews} reviews from {csv_file} using {encoding} encoding")
                        break
                        
                except Exception as e:
                    print(f"Failed to load {csv_file} with {encoding} encoding: {str(e)}")
                    continue
            
            if not file_loaded:
                print(f"Could not load {csv_file} with any encoding")
                
        except Exception as e:
            print(f"Error loading {csv_file}: {str(e)}")
    else:
        print(f"File {csv_file} not found")
    
    return reviews

def extract_keywords(text):
    """Extract keywords from text"""
    if not text:
        return []
    
    # Simple keyword extraction
    import re
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filter out common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}
    
    keywords = [word for word in words if len(word) > 2 and word not in stop_words]
    return keywords[:10]  # Return top 10 keywords

def get_top_keywords(reviews, limit=20):
    """Get top keywords from reviews"""
    keyword_counts = {}
    
    for review in reviews:
        # Use existing keywords if available
        if review.get('keywords'):
            try:
                # Parse existing keywords (format: "keyword1:count1, keyword2:count2")
                keyword_pairs = review['keywords'].split(',')
                for pair in keyword_pairs:
                    if ':' in pair:
                        keyword, count = pair.split(':', 1)
                        keyword = keyword.strip()
                        try:
                            count = int(count.strip())
                            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + count
                        except ValueError:
                            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
                    else:
                        keyword = pair.strip()
                        if keyword:
                            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
            except:
                # Fallback: extract keywords from review text
                keywords = extract_keywords(review.get('review_text', ''))
                for keyword in keywords:
                    keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        else:
            # Extract keywords from review text
            keywords = extract_keywords(review.get('review_text', ''))
            for keyword in keywords:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
    
    # Sort by count and return top keywords
    sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_keywords[:limit]

def get_category_sentiment_data(reviews):
    """Get sentiment data by category"""
    categories = ['room_quality', 'service_staff', 'food_dining', 'location', 'facilities', 'digital_experience', 'business_services']
    category_data = {cat: {'positive': 0, 'negative': 0, 'neutral': 0} for cat in categories}
    
    for review in reviews:
        sentiment = review.get('sentiment', 0)
        review_categories = review.get('categories', '')
        
        # Parse categories (handle multiple categories per review)
        category_list = []
        if review_categories:
            # Split by various delimiters
            for delimiter in [';', ',', ' and ', ' & ']:
                if delimiter in review_categories:
                    category_list = [cat.strip().lower() for cat in review_categories.split(delimiter)]
                    break
            
            if not category_list:
                category_list = [review_categories.strip().lower()]
        
        # Map to standard categories
        mapped_categories = []
        for cat in category_list:
            clean_cat = cat.strip().lower()
            if any(keyword in clean_cat for keyword in ['room', 'bed', 'bathroom', 'clean', 'comfort', 'space', 'size']):
                mapped_categories.append('room_quality')
            elif any(keyword in clean_cat for keyword in ['business', 'meeting', 'conference', 'corporate', 'work', 'office']):
                mapped_categories.append('business_services')
            elif any(keyword in clean_cat for keyword in ['service', 'staff', 'concierge', 'reception', 'hospitality', 'helpful', 'friendly']):
                mapped_categories.append('service_staff')
            elif any(keyword in clean_cat for keyword in ['food', 'dining', 'restaurant', 'breakfast', 'meal', 'cuisine', 'bar']):
                mapped_categories.append('food_dining')
            elif any(keyword in clean_cat for keyword in ['location', 'area', 'neighborhood', 'access', 'convenient', 'central', 'near']):
                mapped_categories.append('location')
            elif any(keyword in clean_cat for keyword in ['facility', 'facilities', 'amenity', 'amenities', 'pool', 'gym', 'spa', 'fitness', 'wellness', 'equipment', 'infrastructure']):
                mapped_categories.append('facilities')
            elif any(keyword in clean_cat for keyword in ['digital', 'online', 'app', 'wifi', 'internet', 'technology', 'booking', 'mobile', 'web', 'electronic']):
                mapped_categories.append('digital_experience')
        
        # If no specific categories found, default to room_quality
        if not mapped_categories:
            mapped_categories = ['room_quality']
        
        # Add review to each identified category
        for category in mapped_categories:
            if category in category_data:
                if sentiment > 0.1:
                    category_data[category]['positive'] += 1
                elif sentiment < -0.1:
                    category_data[category]['negative'] += 1
                else:
                    category_data[category]['neutral'] += 1
    
    return category_data

def get_year_over_year_data(reviews):
    """Get year-over-year trend data"""
    yearly_data = {}
    
    for review in reviews:
        date_str = review.get('date', '')
        if not date_str:
            continue
            
        try:
            # Handle different date formats
            if '/' in date_str:
                # Format: M/D/YYYY or MM/DD/YYYY
                date_obj = datetime.strptime(date_str, '%m/%d/%Y')
            else:
                # Format: YYYY-MM-DD
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            
            year = date_obj.year
            if year not in yearly_data:
                yearly_data[year] = {'positive': 0, 'negative': 0, 'neutral': 0, 'total': 0}
            
            sentiment = review.get('sentiment', 0)
            if sentiment > 0.1:
                yearly_data[year]['positive'] += 1
            elif sentiment < -0.1:
                yearly_data[year]['negative'] += 1
            else:
                yearly_data[year]['neutral'] += 1
            
            yearly_data[year]['total'] += 1
            
        except ValueError:
            continue
    
    return yearly_data

def filter_by_date(reviews, start_date=None, end_date=None):
    """Filter reviews by date range"""
    if not start_date and not end_date:
        return reviews
    
    filtered_reviews = []
    for review in reviews:
        date_str = review.get('date', '')
        if not date_str:
            continue
            
        try:
            if '/' in date_str:
                date_obj = datetime.strptime(date_str, '%m/%d/%Y')
            else:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            
            if start_date and date_obj < start_date:
                continue
            if end_date and date_obj > end_date:
                continue
                
            filtered_reviews.append(review)
        except ValueError:
            continue
    
    return filtered_reviews

def filter_trend_by_hotel_city(reviews, hotel_filter=None, city_filter=None):
    """Filter trend data by hotel or city"""
    if not hotel_filter and not city_filter:
        # Aggregate all data into "Total (All Hotels)"
        return get_year_over_year_data(reviews)
    
    filtered_reviews = []
    for review in reviews:
        if hotel_filter and hotel_filter != 'all' and review.get('hotel_name', '').lower() != hotel_filter.lower():
            continue
        if city_filter and city_filter != 'all' and review.get('city', '').lower() != city_filter.lower():
            continue
        filtered_reviews.append(review)
    
    return get_year_over_year_data(filtered_reviews)

def get_data(hotel_filter=None, city_filter=None, search_filter=None, start_date=None, end_date=None):
    """Get filtered data for dashboard"""
    global reviews_data
    
    # Filter by date range
    filtered_reviews = filter_by_date(reviews_data, start_date, end_date)
    
    # Apply other filters
    if hotel_filter and hotel_filter != 'all':
        filtered_reviews = [r for r in filtered_reviews if r.get('hotel_name', '').lower() == hotel_filter.lower()]
    
    if city_filter and city_filter != 'all':
        filtered_reviews = [r for r in filtered_reviews if r.get('city', '').lower() == city_filter.lower()]
    
    if search_filter:
        search_lower = search_filter.lower()
        filtered_reviews = [r for r in filtered_reviews if search_lower in r.get('review_text', '').lower()]
    
    # Calculate KPIs
    total_reviews = len(filtered_reviews)
    positive_reviews = len([r for r in filtered_reviews if r.get('sentiment', 0) > 0.1])
    negative_reviews = len([r for r in filtered_reviews if r.get('sentiment', 0) < -0.1])
    neutral_reviews = len([r for r in filtered_reviews if -0.1 <= r.get('sentiment', 0) <= 0.1])
    
    positive_percentage = (positive_reviews / total_reviews * 100) if total_reviews > 0 else 0
    negative_percentage = (negative_reviews / total_reviews * 100) if total_reviews > 0 else 0
    net_sentiment = positive_percentage - negative_percentage
    
    # Get unique hotels and cities
    hotels = sorted(list(set([r.get('hotel_name', '') for r in filtered_reviews if r.get('hotel_name')])))
    cities = sorted(list(set([r.get('city', '') for r in filtered_reviews if r.get('city')])))
    
    # Get top keywords
    top_keywords = get_top_keywords(filtered_reviews)
    
    # Get category sentiment data
    category_data = get_category_sentiment_data(filtered_reviews)
    
    # Get trend data (always use full dataset, not date-filtered)
    trend_data = filter_trend_by_hotel_city(reviews_data, hotel_filter, city_filter)
    
    # Prepare table data (limit to 20 rows for performance)
    table_data = []
    for review in filtered_reviews[:20]:
        table_data.append({
            'hotel_name': review.get('hotel_name', ''),
            'city': review.get('city', ''),
            'review_text': review.get('review_text', '')[:200] + '...' if len(review.get('review_text', '')) > 200 else review.get('review_text', ''),
            'sentiment': review.get('sentiment', 0),
            'rating': review.get('rating', 0),
            'date': review.get('date', ''),
            'categories': review.get('categories', ''),
            'keywords': review.get('keywords', '')
        })
    
    return {
        'total_reviews': total_reviews,
        'positive_reviews': positive_reviews,
        'negative_reviews': negative_reviews,
        'neutral_reviews': neutral_reviews,
        'positive_percentage': round(positive_percentage, 1),
        'negative_percentage': round(negative_percentage, 1),
        'net_sentiment': round(net_sentiment, 1),
        'hotels': hotels,
        'cities': cities,
        'top_keywords': top_keywords,
        'category_data': category_data,
        'trend_data': trend_data,
        'table_data': table_data,
        'last_updated': last_updated.isoformat() if last_updated else None
    }

# Load data on startup
try:
    reviews_data = load_real_data()
    last_updated = datetime.now()
    print(f"Data loaded successfully: {len(reviews_data)} reviews")
except Exception as e:
    print(f"Error loading data: {str(e)}")
    reviews_data = []
    last_updated = datetime.now()

@app.route('/')
def index():
    """Serve the main dashboard"""
    try:
        with open('ai_hospitality_sentiment_dashboard.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        return html_content
    except Exception as e:
        return f"Error loading dashboard: {str(e)}", 500

@app.route('/api/data')
def api_data():
    """API endpoint for dashboard data"""
    hotel_filter = request.args.get('hotel', 'all')
    city_filter = request.args.get('city', 'all')
    search_filter = request.args.get('search', '')
    
    # Parse date filters
    start_date = None
    end_date = None
    
    start_date_str = request.args.get('startDate', '')
    end_date_str = request.args.get('endDate', '')
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        except ValueError:
            pass
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError:
            pass
    
    data = get_data(hotel_filter, city_filter, search_filter, start_date, end_date)
    return jsonify(data)

@app.route('/api/keyword-search')
def keyword_search():
    """Search for reviews containing specific keywords"""
    keyword = request.args.get('keyword', '')
    if not keyword:
        return jsonify({'reviews': [], 'count': 0})
    
    # Search in full dataset
    matching_reviews = []
    for review in reviews_data:
        if keyword.lower() in review.get('review_text', '').lower():
            matching_reviews.append({
                'hotel_name': review.get('hotel_name', ''),
                'city': review.get('city', ''),
                'review_text': review.get('review_text', ''),
                'sentiment': review.get('sentiment', 0),
                'rating': review.get('rating', 0),
                'date': review.get('date', ''),
                'categories': review.get('categories', ''),
                'keywords': review.get('keywords', '')
            })
    
    # Limit results
    matching_reviews = matching_reviews[:50]
    
    return jsonify({
        'reviews': matching_reviews,
        'count': len(matching_reviews)
    })

@app.route('/api/negative-reviews')
def get_negative_reviews():
    """Get negative reviews grouped by category"""
    negative_reviews = [r for r in reviews_data if r.get('sentiment', 0) < -0.1]
    
    # Group by category
    category_reviews = {}
    categories = ['room_quality', 'service_staff', 'food_dining', 'location', 'facilities', 'digital_experience', 'business_services']
    
    for category in categories:
        category_reviews[category] = []
    
    for review in negative_reviews:
        review_categories = review.get('categories', '')
        category_list = []
        
        if review_categories:
            for delimiter in [';', ',', ' and ', ' & ']:
                if delimiter in review_categories:
                    category_list = [cat.strip().lower() for cat in review_categories.split(delimiter)]
                    break
            
            if not category_list:
                category_list = [review_categories.strip().lower()]
        
        # Map to standard categories
        mapped_categories = []
        for cat in category_list:
            clean_cat = cat.strip().lower()
            if any(keyword in clean_cat for keyword in ['room', 'bed', 'bathroom', 'clean', 'comfort', 'space', 'size']):
                mapped_categories.append('room_quality')
            elif any(keyword in clean_cat for keyword in ['business', 'meeting', 'conference', 'corporate', 'work', 'office']):
                mapped_categories.append('business_services')
            elif any(keyword in clean_cat for keyword in ['service', 'staff', 'concierge', 'reception', 'hospitality', 'helpful', 'friendly']):
                mapped_categories.append('service_staff')
            elif any(keyword in clean_cat for keyword in ['food', 'dining', 'restaurant', 'breakfast', 'meal', 'cuisine', 'bar']):
                mapped_categories.append('food_dining')
            elif any(keyword in clean_cat for keyword in ['location', 'area', 'neighborhood', 'access', 'convenient', 'central', 'near']):
                mapped_categories.append('location')
            elif any(keyword in clean_cat for keyword in ['facility', 'facilities', 'amenity', 'amenities', 'pool', 'gym', 'spa', 'fitness', 'wellness', 'equipment', 'infrastructure']):
                mapped_categories.append('facilities')
            elif any(keyword in clean_cat for keyword in ['digital', 'online', 'app', 'wifi', 'internet', 'technology', 'booking', 'mobile', 'web', 'electronic']):
                mapped_categories.append('digital_experience')
        
        if not mapped_categories:
            mapped_categories = ['room_quality']
        
        for category in mapped_categories:
            if category in category_reviews:
                category_reviews[category].append(review)
    
    # Limit results
    limited_category_reviews = {}
    for category, reviews in category_reviews.items():
        limited_category_reviews[category] = reviews[:10]
    
    return jsonify({
        'category_reviews': limited_category_reviews,
        'total_negative_reviews': len(negative_reviews)
    })

@app.route('/api/refresh')
def refresh_data():
    """Refresh data from source"""
    global last_updated, reviews_data
    reviews_data = load_real_data()
    last_updated = datetime.now()
    return jsonify({'status': 'success', 'message': 'Data refreshed successfully'})

# Vercel entry point
def handler(request):
    return app(request.environ, lambda *args: None)

# For local development
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
