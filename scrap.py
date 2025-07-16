import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class RedditUserScraper:
    def __init__(self, headless=True):
        """Initialize the Reddit scraper with Chrome driver"""
        self.driver = None
        self.setup_driver(headless)
    
    def setup_driver(self, headless=True):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
    
    def scrape_user_posts(self, username, max_posts=30):
        """Scrape posts from a Reddit user's profile"""
        url = f"https://www.reddit.com/user/{username}/submitted/"
        print(f"Scraping posts from: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(5)

            page_title = self.driver.title
            print(f"Page title: {page_title}")
            
            try:
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                print("Page body loaded successfully")
            except TimeoutException:
                print("Page failed to load properly")
                return []
            
            post_selectors = [
                '[data-testid="post-container"]',
                'div[data-click-id="body"]',
                'div[data-testid="post"]',
                'article',
                'div.Post',
                'div[role="article"]',
                'div.thing',
                'shreddit-post'
            ]
            
            posts_data = []
            scroll_count = 0
            max_scrolls = 10
            
            while len(posts_data) < max_posts and scroll_count < max_scrolls:
                posts = []
                
                # Try different selectors
                for selector in post_selectors:
                    posts = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if posts:
                        print(f"Found {len(posts)} posts using selector: {selector}")
                        break
                
                if not posts:
                    print("No posts found with any selector. Checking page source...")
                    # Check if we're on the right page
                    if "User not found" in self.driver.page_source or "doesn't exist" in self.driver.page_source:
                        print("User doesn't exist or profile is private")
                        return []
                    
                    # Print some of the page source for debugging
                    print("Page source preview:")
                    print(self.driver.page_source[:500])
                    break
                
                for post in posts[len(posts_data):]:
                    try:
                        # Extract post data
                        post_data = self.extract_post_data(post)
                        if post_data:
                            posts_data.append(post_data)
                        
                        if len(posts_data) >= max_posts:
                            break
                            
                    except Exception as e:
                        print(f"Error extracting post data: {e}")
                        continue
                
                # Scroll to load more posts
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                scroll_count += 1
                
                # Check if we've reached the end
                new_posts = []
                for selector in post_selectors:
                    new_posts = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if new_posts:
                        break
                
                if len(new_posts) == len(posts):
                    print("No new posts found after scrolling")
                    break
            
            return posts_data
            
        except TimeoutException:
            print(f"Timeout loading user profile for {username}")
            return []
        except Exception as e:
            print(f"Error scraping posts: {e}")
            return []
    
    def extract_post_data(self, post_element):
        """Extract data from a single post element"""
        try:
            post_data = {}
            
            # Title - try multiple selectors
            title_selectors = [
                '[data-testid="post-content"] h3',
                'h3',
                'h2',
                'h1',
                '[data-adclicklocation="title"]',
                '.title a',
                'a[data-click-id="body"]',
                'shreddit-post h1',
                '[slot="title"]'
            ]
            
            for selector in title_selectors:
                try:
                    title_element = post_element.find_element(By.CSS_SELECTOR, selector)
                    post_data['title'] = title_element.text.strip()
                    break
                except NoSuchElementException:
                    continue
            
            if 'title' not in post_data:
                post_data['title'] = "No title found"
            
            # Post content/text - try multiple selectors for full post content
            content_selectors = [
                '[data-testid="post-content"] div[data-testid="post-text"]',
                'div[data-testid="post-text"]',
                '[data-click-id="text"]',
                'div.usertext-body',
                'div[data-testid="post-text-container"]',
                'shreddit-post div[slot="text-body"]',
                'div.RichTextJSON-root',
                'div[data-testid="post-rtjson-content"]',
                'div.s-prose',
                'div[data-adclicklocation="media"]',
                'div.Post__content',
                'div[data-testid="post-content"] > div:last-child',
                'p'
            ]
            
            post_content = ""
            for selector in content_selectors:
                try:
                    content_elements = post_element.find_elements(By.CSS_SELECTOR, selector)
                    if content_elements:
                        for elem in content_elements:
                            text = elem.text.strip()
                            if text and len(text) > 10:  # Only consider substantial text
                                post_content += text + "\n"
                        if post_content.strip():
                            break
                except NoSuchElementException:
                    continue
            
            # If no content found, try to get any text content from the post
            if not post_content.strip():
                try:
                    all_text = post_element.text
                    lines = all_text.split('\n')
                    # Skip title and metadata, look for content
                    for i, line in enumerate(lines):
                        if line.strip() and len(line) > 50:  # Likely content
                            post_content = line.strip()
                            break
                except:
                    pass
            
            post_data['content'] = post_content.strip() if post_content.strip() else "No content found"
            
            subreddit_selectors = [
                '[data-testid="subreddit-name"]',
                '.subreddit',
                'a[href*="/r/"]',
                'span[data-testid="subreddit-name"]'
            ]
            
            for selector in subreddit_selectors:
                try:
                    subreddit_element = post_element.find_element(By.CSS_SELECTOR, selector)
                    post_data['subreddit'] = subreddit_element.text.strip()
                    break
                except NoSuchElementException:
                    continue
            
            if 'subreddit' not in post_data:
                post_data['subreddit'] = "Unknown"
            
            # Score/Upvotes - try multiple selectors 
            print(f"Extracted post: {post_data.get('title', 'No title')[:50]}...")
            print(f"Content length: {len(post_data.get('content', ''))}")
            
            return post_data
            
        except Exception as e:
            print(f"Error extracting post data: {e}")
            return None
    
    def scrape_user_comments(self, username, max_comments=50):
        """Scrape comments from a Reddit user's profile"""
        url = f"https://www.reddit.com/user/{username}/comments/"
        print(f"Scraping comments from: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(5)
            
            # Debug: Check if page loaded correctly
            page_title = self.driver.title
            print(f"Page title: {page_title}")
            
            # Wait for page to load
            try:
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                print("Page body loaded successfully")
            except TimeoutException:
                print("Page failed to load properly")
                return []
            
            # Try multiple selectors for comments
            comment_selectors = [
                '[data-testid="comment"]',
                'div[data-testid="comment-tree-item"]',
                'div.Comment',
                'div[role="article"]',
                'div.thing[data-type="comment"]',
                'shreddit-comment',
                'div[data-testid="comment-body-header"]',
                'div.Comment__body',
                'article[data-testid="comment"]',
                'div.usertext',
                'div[id*="thing_t1_"]'
            ]
            
            comments_data = []
            scroll_count = 0
            max_scrolls = 15
            
            while len(comments_data) < max_comments and scroll_count < max_scrolls:
                comments = []
                
                # Try different selectors
                for selector in comment_selectors:
                    comments = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if comments:
                        print(f"Found {len(comments)} comments using selector: {selector}")
                        break
                
                if not comments:
                    print("No comments found with any selector.")
                    
                    # Try alternative approach - look for comment patterns in page source
                    page_source = self.driver.page_source
                    if "comment" in page_source.lower() or "usertext" in page_source.lower():
                        print("Page contains comment-related content, trying alternative selectors...")
                        
                        # Try broader selectors
                        alternative_selectors = [
                            'div[data-type="comment"]',
                            'div.usertext-body',
                            'div[class*="comment"]',
                            'div[class*="Comment"]',
                            'p'
                        ]
                        
                        for selector in alternative_selectors:
                            comments = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if comments:
                                print(f"Found {len(comments)} elements with alternative selector: {selector}")
                                break
                    
                    if not comments:
                        # Check if we're on the right page
                        if "User not found" in page_source or "doesn't exist" in page_source:
                            print("User doesn't exist or profile is private")
                            return []
                        
                        print("Still no comments found. Page source preview:")
                        print(page_source[:1000])
                        break
                
                # Process found comments
                new_comments_found = 0
                for comment in comments[len(comments_data):]:
                    try:
                        # Extract comment data
                        comment_data = self.extract_comment_data(comment)
                        if comment_data and comment_data.get('text', '').strip() not in ['No text found', '']:
                            comments_data.append(comment_data)
                            new_comments_found += 1
                        
                        if len(comments_data) >= max_comments:
                            break
                            
                    except Exception as e:
                        print(f"Error extracting comment data: {e}")
                        continue
                
                print(f"Added {new_comments_found} new comments, total: {len(comments_data)}")
                
                # Scroll to load more comments
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                scroll_count += 1
                
                # Check if we've reached the end
                new_comments = []
                for selector in comment_selectors:
                    new_comments = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if new_comments:
                        break
                
                if len(new_comments) <= len(comments):
                    print("No new comments found after scrolling")
                    break
            
            return comments_data
            
        except TimeoutException:
            print(f"Timeout loading user comments for {username}")
            return []
        except Exception as e:
            print(f"Error scraping comments: {e}")
            return []
    
    def extract_comment_data(self, comment_element):
        """Extract data from a single comment element"""
        try:
            comment_data = {}
            
            # Comment text - try multiple selectors
            text_selectors = [
                '[data-testid="comment-text"]',
                'div[data-testid="comment-text"]',
                'div.usertext-body',
                'div.Comment__body',
                'div[data-testid="comment-text-container"]',
                'shreddit-comment div[slot="comment-body"]',
                'div.RichTextJSON-root',
                'div[data-testid="comment-rtjson-content"]',
                'div.s-prose',
                'div.md',
                'p',
                'div.Comment__body .RichTextJSON-root'
            ]
            
            comment_text = ""
            for selector in text_selectors:
                try:
                    text_elements = comment_element.find_elements(By.CSS_SELECTOR, selector)
                    if text_elements:
                        for elem in text_elements:
                            text = elem.text.strip()
                            if text and len(text) > 5:  # Only consider substantial text
                                comment_text += text + "\n"
                        if comment_text.strip():
                            break
                except NoSuchElementException:
                    continue
            
            if not comment_text.strip():
                try:
                    all_text = comment_element.text
                    lines = all_text.split('\n')

                    for line in lines:
                        if line.strip() and len(line) > 20:
                            comment_text = line.strip()
                            break
                except:
                    pass
            
            comment_data['text'] = comment_text.strip() if comment_text.strip() else "No text found"
            
            print(f"Extracted comment: {comment_data.get('text', 'No text')[:50]}...")
            
            return comment_data
            
        except Exception as e:
            print(f"Error extracting comment data: {e}")
            return None
    
    def get_json(self, data):
        return json.dumps(data, indent=2, ensure_ascii=False) 
    
    def close(self):
        """Close the browser driver"""
        if self.driver:
            self.driver.quit()

def main(username):
    
    if not username:
        print("Username cannot be empty!")
        return
    
    scraper = RedditUserScraper(headless=False)  # Set to True for headless mode
    
    try:
        print(f"Scraping data for user: {username}")
        
        # Scrape posts
        posts = scraper.scrape_user_posts(username, max_posts=20)
        print(f"Found {len(posts)} posts")
        
        # Scrape comments
        comments = scraper.scrape_user_comments(username, max_comments=30)
        print(f"Found {len(comments)} comments")
       
        if posts:
            posts = scraper.get_json(posts)
        
        if comments:
            comments = scraper.get_json(comments)
        
        print("Scraping completed!")
    
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        scraper.close() 
    
    return posts, comments 
