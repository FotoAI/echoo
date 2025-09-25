import aiohttp
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models import UserInstaPost
from app.schemas import InstagramPostCreate
import os

logger = logging.getLogger(__name__)

class InstagramService:
    def __init__(self):
        self.api_url = "https://instagram-scraper-stable-api.p.rapidapi.com/get_ig_user_posts.php"
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "x-rapidapi-host": "instagram-scraper-stable-api.p.rapidapi.com",
            "x-rapidapi-key": os.environ.get("INSTA_FETCH_KEY")
        }
    
    def _clean_none_keys(self, data):
        """
        Recursively clean None keys from dictionaries to prevent JSON serialization errors
        """
        if isinstance(data, dict):
            # Filter out None keys and recursively clean values
            cleaned = {}
            for key, value in data.items():
                if key is not None:
                    cleaned[key] = self._clean_none_keys(value)
            return cleaned
        elif isinstance(data, list):
            # Recursively clean list items
            return [self._clean_none_keys(item) for item in data]
        else:
            # Return primitive values as-is
            return data
    
    async def fetch_user_posts(self, instagram_url: str, amount: int = 10) -> Optional[dict]:
        """
        Fetch Instagram posts for a given user URL
        """
        try:
            data = {
                "username_or_url": instagram_url,
                "amount": str(amount)
            }
            
            timeout = aiohttp.ClientTimeout(total=30.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.api_url,
                    headers=self.headers,
                    data=data
                ) as response:
                    response.raise_for_status()
                    json_response = await response.json()
                    
                    # Validate and clean the response to prevent None key issues
                    if isinstance(json_response, dict):
                        # Recursively clean None keys from the response
                        json_response = self._clean_none_keys(json_response)
                    
                    return json_response
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error fetching Instagram posts: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching Instagram posts: {e}")
            return None
    
    def extract_posts_from_response(self, api_response: dict) -> List[dict]:
        """
        Extract post data from Instagram API response
        """
        posts = []
        
        if not api_response or "posts" not in api_response:
            return posts
        
        try:
            for post_node in api_response["posts"]:
                if not isinstance(post_node, dict) or "node" not in post_node:
                    continue
                    
                node = post_node["node"]
                if not isinstance(node, dict):
                    continue
                
                # Safely extract code, ensuring it's not None
                code = node.get("code")
                if not code or not isinstance(code, str):
                    logger.warning("Skipping post with invalid or missing code")
                    continue
                
                post_data = {
                    "code": code,
                    "caption": None,
                    "instagram_created_at": None
                }
                
                # Extract caption text safely
                if "caption" in node and node["caption"] is not None:
                    caption_data = node["caption"]
                    if isinstance(caption_data, dict):
                        # Check if caption dict has None keys and filter them out
                        if any(key is None for key in caption_data.keys()):
                            logger.warning("Found None keys in caption data, filtering them out")
                            caption_data = {k: v for k, v in caption_data.items() if k is not None}
                        
                        if "text" in caption_data and caption_data["text"]:
                            post_data["caption"] = caption_data["text"]
                    elif isinstance(caption_data, str):
                        post_data["caption"] = caption_data
                
                # Extract created_at timestamp safely
                if "taken_at" in node and node["taken_at"] is not None:
                    post_data["instagram_created_at"] = node["taken_at"]
                elif ("caption" in node and node["caption"] and 
                      isinstance(node["caption"], dict) and 
                      "created_at" in node["caption"]):
                    caption_data = node["caption"]
                    if caption_data["created_at"] is not None:
                        post_data["instagram_created_at"] = caption_data["created_at"]
                
                posts.append(post_data)
                
        except Exception as e:
            logger.error(f"Error extracting posts from Instagram API response: {e}")
            logger.error(f"API response structure: {api_response}")
            return []
        
        return posts
    
    def get_existing_post_codes(self, db: Session, user_id: int) -> set:
        """
        Get set of existing post codes for a user
        """
        existing_posts = db.query(UserInstaPost.code).filter(
            UserInstaPost.user_id == user_id
        ).all()
        return {post.code for post in existing_posts}
    
    def save_new_posts(self, db: Session, user_id: int, posts: List[dict]) -> dict:
        """
        Save new Instagram posts to database
        """
        existing_codes = self.get_existing_post_codes(db, user_id)
        
        new_posts = []
        skipped_count = 0
        
        for post in posts:
            if post["code"] not in existing_codes:
                insta_post = UserInstaPost(
                    user_id=user_id,
                    caption=post["caption"],
                    code=post["code"],
                    instagram_created_at=post["instagram_created_at"]
                )
                new_posts.append(insta_post)
            else:
                skipped_count += 1
        
        if new_posts:
            db.add_all(new_posts)
            db.commit()
            
            # Refresh to get IDs
            for post in new_posts:
                db.refresh(post)
        
        return {
            "total_received": len(posts),
            "new_posts": len(new_posts),
            "skipped_posts": skipped_count,
            "posts": new_posts
        }
    
    async def fetch_and_save_user_posts(self, db: Session, user_id: int, instagram_url: str) -> dict:
        """
        Fetch Instagram posts and save new ones to database
        """
        # Fetch posts from Instagram API
        api_response = await self.fetch_user_posts(instagram_url)
        
        if not api_response:
            return {
                "success": False,
                "error": "Failed to fetch posts from Instagram API",
                "total_received": 0,
                "new_posts": 0,
                "skipped_posts": 0
            }
        
        # Extract post data
        posts = self.extract_posts_from_response(api_response)
        
        if not posts:
            return {
                "success": True,
                "message": "No posts found in API response",
                "total_received": 0,
                "new_posts": 0,
                "skipped_posts": 0
            }
        
        # Save new posts
        result = self.save_new_posts(db, user_id, posts)
        
        return {
            "success": True,
            "message": f"Successfully processed {result['total_received']} posts",
            **result
        }

# Create a singleton instance
instagram_service = InstagramService()
