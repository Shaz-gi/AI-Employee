#!/usr/bin/env python3
"""
Simple LinkedIn Poster - Direct approach that works
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, 'src')

from playwright.sync_api import sync_playwright

def post_to_linkedin(content):
    """Post to LinkedIn with simple, direct approach."""
    
    session_path = Path('linkedin_session')
    session_path.mkdir(exist_ok=True)
    
    print("🔗 Opening LinkedIn...")
    
    with sync_playwright() as p:
        # Launch browser
        context = p.chromium.launch_persistent_context(
            str(session_path),
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        page = context.pages[0]
        
        # Go to feed
        print("📝 Going to LinkedIn feed...")
        page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(5000)  # Wait for load
        
        print("⏳ Waiting 10 seconds for you to verify page loaded...")
        page.wait_for_timeout(10000)
        
        # Find "Start a post" - try multiple approaches
        print("🔍 Finding 'Start a post'...")
        
        # Approach 1: Click by text content
        try:
            # Find any element with "Start a post" text and click it
            page.locator('text="Start a post"').first.click()
            print("✅ Clicked 'Start a post' by text")
            page.wait_for_timeout(3000)
        except Exception as e:
            print(f"⚠️  First approach failed: {e}")
            # Approach 2: Click the share box area
            try:
                page.click('div.share-box-feed-entry__trigger')
                print("✅ Clicked share box")
                page.wait_for_timeout(3000)
            except Exception as e2:
                print(f"⚠️  Second approach failed: {e2}")
                print("❌ Could not open post dialog")
                page.screenshot(path='linkedin_error.png')
                print("Screenshot saved: linkedin_error.png")
                context.close()
                return False
        
        # Type content
        print("📝 Typing content...")
        page.wait_for_timeout(2000)
        
        # Find text area and type
        try:
            text_area = page.locator('div[contenteditable="true"]').first
            text_area.click()
            page.wait_for_timeout(1000)
            text_area.fill(content)
            print("✅ Content entered")
            page.wait_for_timeout(2000)
        except Exception as e:
            print(f"❌ Could not enter content: {e}")
            page.screenshot(path='linkedin_text_error.png')
            context.close()
            return False
        
        # Click Post button
        print("📝 Clicking Post button...")
        try:
            post_btn = page.locator('button:has-text("Post")').first
            post_btn.click()
            print("✅ Post button clicked!")
            
            # Complete the posting cycle TWICE
            for cycle in range(1, 3):  # 2 cycles
                print(f"\n🔄 CYCLE {cycle}/2")
                print("=" * 40)
                
                # Wait for options dialog
                print("⏳ Waiting for options dialog...")
                page.wait_for_timeout(5000)
                
                # Look for options and select one (e.g., "Anyone", "Connections", etc.)
                print("🔍 Looking for visibility options...")
                try:
                    options_selectors = [
                        'text="Anyone"',
                        'text="Connections"',
                        'text="Your network"',
                        'div.ember-view[role="option"]',
                        'button[aria-label*="Anyone"]',
                        'button:has-text("Anyone")'
                    ]
                    
                    option_clicked = False
                    for selector in options_selectors:
                        try:
                            option = page.locator(selector).first
                            if option.is_visible():
                                option.click()
                                print(f"✅ Selected option: {selector}")
                                option_clicked = True
                                page.wait_for_timeout(2000)
                                break
                        except:
                            continue
                    
                    if not option_clicked:
                        print("⚠️  Trying to click any option...")
                        try:
                            any_option = page.locator('div[role="option"]').first
                            any_option.click()
                            print("✅ Clicked first option")
                            page.wait_for_timeout(2000)
                        except:
                            print("⚠️  Could not find options")
                            
                except Exception as e:
                    print(f"⚠️  Options step error: {e}")
                
                # Look for "Done" button
                print("🔍 Looking for Done button...")
                page.wait_for_timeout(3000)
                
                try:
                    done_btn = page.locator('button:has-text("Done")').first
                    done_btn.click()
                    print("✅ Clicked Done button!")
                    page.wait_for_timeout(3000)
                except:
                    print("⚠️  Could not find Done button")
                
                # Look for final Post button
                print("🔍 Looking for Post button...")
                page.wait_for_timeout(2000)
                
                try:
                    final_post = page.locator('button:has-text("Post")').first
                    final_post.click()
                    print("✅ Clicked Post button!")
                    
                    if cycle == 1:
                        print("⏳ Waiting before cycle 2...")
                        page.wait_for_timeout(5000)
                    else:
                        print("⏳ Waiting for post to submit...")
                        page.wait_for_timeout(10000)
                        
                except:
                    print("⚠️  Could not find Post button")
                    if cycle == 1:
                        break  # Can't continue to cycle 2
            
            print("\n✅ All cycles complete! Check your LinkedIn profile")
            
            # Save confirmation
            page.screenshot(path='linkedin_posted.png')
            print("Screenshot saved: linkedin_posted.png")
            
            context.close()
            return True
            
        except Exception as e:
            print(f"❌ Could not complete post: {e}")
            page.screenshot(path='linkedin_post_error.png')
            print("Screenshot saved: linkedin_post_error.png")
            context.close()
            return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simple_linkedin.py \"Your post content here\"")
        sys.exit(1)
    
    content = ' '.join(sys.argv[1:])
    
    print("🤖 Simple LinkedIn Poster")
    print("=" * 50)
    print(f"Content: {content}")
    print("=" * 50)
    
    success = post_to_linkedin(content)
    
    if success:
        print("\n🎉 SUCCESS! Your post should be on LinkedIn now!")
    else:
        print("\n❌ Failed - check screenshots for debugging")
