# backend/app/utils/google_chat.py
"""
Google Chat Webhook Integration for ParkEase
Send notifications to users via Google Chat
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional

def send_google_chat_message(webhook_url: str, message: str, title: Optional[str] = None) -> Dict:
    """
    Send a simple text message to Google Chat
    
    Args:
        webhook_url: Google Chat webhook URL
        message: Message text to send
        title: Optional title for the message
        
    Returns:
        Dictionary with status and response
    """
    try:
        payload = {"text": message}
        
        response = requests.post(
            webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json; charset=UTF-8'},
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": "Message sent successfully",
                "response": response.text
            }
        else:
            return {
                "success": False,
                "error": f"Failed with status {response.status_code}",
                "response": response.text
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def send_google_chat_card(webhook_url: str, card_data: Dict) -> Dict:
    """
    Send a rich card message to Google Chat
    
    Args:
        webhook_url: Google Chat webhook URL
        card_data: Dictionary containing card information
        
    Returns:
        Dictionary with status and response
    """
    try:
        payload = {
            "cards": [
                {
                    "header": {
                        "title": card_data.get("title", "ParkEase Notification"),
                        "subtitle": card_data.get("subtitle", ""),
                        "imageUrl": card_data.get("image_url", "https://developers.google.com/chat/images/quickstart-app-avatar.png")
                    },
                    "sections": card_data.get("sections", [])
                }
            ]
        }
        
        response = requests.post(
            webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json; charset=UTF-8'},
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": "Card sent successfully",
                "response": response.text
            }
        else:
            return {
                "success": False,
                "error": f"Failed with status {response.status_code}",
                "response": response.text
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def send_parking_reminder(webhook_url: str, user_name: str, available_spots: int, new_lots: List[str] = None) -> Dict:
    """
    Send a parking reminder card to Google Chat
    
    Args:
        webhook_url: Google Chat webhook URL
        user_name: Name of the user
        available_spots: Number of available parking spots
        new_lots: List of new parking lot names (optional)
        
    Returns:
        Dictionary with status and response
    """
    
    # Build sections for the card
    sections = []
    
    # Main message section
    widgets = [
        {
            "textParagraph": {
                "text": f"<b>Hi {user_name}!</b> 👋<br><br>We noticed you haven't booked a parking spot recently. Don't miss out on convenient parking!"
            }
        }
    ]
    
    # Available spots info
    if available_spots > 0:
        widgets.append({
            "keyValue": {
                "topLabel": "Available Spots",
                "content": str(available_spots),
                "contentMultiline": False,
                "icon": "PARKING"
            }
        })
    
    sections.append({"widgets": widgets})
    
    # New lots section (if any)
    if new_lots and len(new_lots) > 0:
        new_lots_widgets = [
            {
                "textParagraph": {
                    "text": "<b>🎉 New Parking Lots Available!</b>"
                }
            }
        ]
        
        for lot in new_lots[:3]:  # Show max 3 new lots
            new_lots_widgets.append({
                "keyValue": {
                    "content": lot,
                    "icon": "MAP_PIN"
                }
            })
        
        sections.append({"widgets": new_lots_widgets})
    
    # Action buttons
    action_widgets = [
        {
            "buttons": [
                {
                    "textButton": {
                        "text": "BOOK NOW",
                        "onClick": {
                            "openLink": {
                                "url": "http://localhost:8080/dashboard?tab=lots"
                            }
                        }
                    }
                }
            ]
        }
    ]
    
    sections.append({"widgets": action_widgets})
    
    # Build card data
    card_data = {
        "title": "🚗 ParkEase Reminder",
        "subtitle": f"Daily Parking Reminder - {datetime.now().strftime('%B %d, %Y')}",
        "sections": sections
    }
    
    return send_google_chat_card(webhook_url, card_data)


def send_new_lot_notification(webhook_url: str, lot_name: str, location: str, available_spots: int, price: float) -> Dict:
    """
    Send notification about a new parking lot
    
    Args:
        webhook_url: Google Chat webhook URL
        lot_name: Name of the parking lot
        location: Location/address
        available_spots: Number of available spots
        price: Price per hour
        
    Returns:
        Dictionary with status and response
    """
    
    card_data = {
        "title": "🎉 New Parking Lot Available!",
        "subtitle": lot_name,
        "sections": [
            {
                "widgets": [
                    {
                        "textParagraph": {
                            "text": f"<b>A new parking lot has been added near you!</b>"
                        }
                    },
                    {
                        "keyValue": {
                            "topLabel": "Location",
                            "content": location,
                            "icon": "MAP_PIN"
                        }
                    },
                    {
                        "keyValue": {
                            "topLabel": "Available Spots",
                            "content": str(available_spots),
                            "icon": "PARKING"
                        }
                    },
                    {
                        "keyValue": {
                            "topLabel": "Price",
                            "content": f"₹{price}/hour",
                            "icon": "INR"
                        }
                    },
                    {
                        "buttons": [
                            {
                                "textButton": {
                                    "text": "VIEW DETAILS",
                                    "onClick": {
                                        "openLink": {
                                            "url": "http://localhost:8080/dashboard?tab=lots"
                                        }
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    return send_google_chat_card(webhook_url, card_data)


def send_booking_confirmation(webhook_url: str, booking_id: str, lot_name: str, spot_number: str, arrival_time: str) -> Dict:
    """
    Send booking confirmation to Google Chat
    
    Args:
        webhook_url: Google Chat webhook URL
        booking_id: Booking ID
        lot_name: Parking lot name
        spot_number: Spot number
        arrival_time: Expected arrival time
        
    Returns:
        Dictionary with status and response
    """
    
    card_data = {
        "title": "✅ Booking Confirmed!",
        "subtitle": f"Booking #{booking_id}",
        "sections": [
            {
                "widgets": [
                    {
                        "textParagraph": {
                            "text": "<b>Your parking spot has been reserved!</b>"
                        }
                    },
                    {
                        "keyValue": {
                            "topLabel": "Parking Lot",
                            "content": lot_name,
                            "icon": "MAP_PIN"
                        }
                    },
                    {
                        "keyValue": {
                            "topLabel": "Spot Number",
                            "content": spot_number,
                            "icon": "PARKING"
                        }
                    },
                    {
                        "keyValue": {
                            "topLabel": "Arrival Time",
                            "content": arrival_time,
                            "icon": "CLOCK"
                        }
                    },
                    {
                        "buttons": [
                            {
                                "textButton": {
                                    "text": "VIEW BOOKING",
                                    "onClick": {
                                        "openLink": {
                                            "url": "http://localhost:8080/dashboard?tab=bookings"
                                        }
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    return send_google_chat_card(webhook_url, card_data)
