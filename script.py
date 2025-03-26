import os, json, time, random, sys, datetime, ast
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
import google.generativeai as genai
from typing import List, Dict

load_dotenv()
username = os.environ.get("IG_USERNAME")
email = os.environ.get("IG_EMAIL")
password = os.environ.get("IG_PASSWORD")
login_only = ast.literal_eval(os.environ.get("LOGIN_ONLY"))
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')


def generate_clapback(comments: List[str], reel_description: str) -> str:
    """Generate a brutal clapback using Gemini AI based on reel comments and description."""
    
    # Ensure we have enough comments
    if not comments:
        return "This reel is so dry I got dust in my eyes 💀"
    
    # Extract top comments for context
    top_comments = comments[:20]  # Top 5 for context
    
    # AI prompt construction
    prompt = f"""
    
    these are comments under a reel : {top_comments} 
    generate a similar comment on your own.
    the comment should be short and under 10 words.
    u are allowed to use slangs and slurs.
    u are allowed to be brutal and mean if required.
    try to be creative and u are allowed to use hinglish if used in comments.
    
    
    """

    # Try generating AI response
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating clapback: {e}")
        # Fallback responses if AI fails
        return ("the ai has failed me it stopped working plz let my developer know that i fucked up :(")



def get_reel_comments(client: Client, reel_id: str) -> List[str]:
    """Fetch top comments from a reel."""
    try:
        comments = client.media_comments(reel_id)
        # Get top 20 comments instead of 10
        return [comment.text for comment in comments[:20]]
    except Exception as e:
        print(f"Error fetching comments: {e}")
        return []

def send_clapback(client: Client, thread_id: str, message: str):
    """Send a clapback message in the DM thread."""
    try:
        client.direct_answer(thread_id, message)
        print(f"[{get_now()}] Sent clapback: {message}")
    except Exception as e:
        print(f"Error sending clapback: {e}")

def authenticate(client, session_file):
    try:
        if os.path.exists(session_file):
            try:
                # Try to load the session file
                client.load_settings(session_file)
                try:
                    # Initialize CSRF token first
                    client.get_settings()
                    client.set_settings({})
                    client.init()
                    
                    # Now try to login
                    client.login(username, password)
                    client.get_timeline_feed()  # check if the session is valid
                except Exception as e:
                    print(f"[{get_now()}] Session invalid, attempting to re-login...")
                    # Delete the old session file
                    if os.path.exists(session_file):
                        os.remove(session_file)
                    # Try logging in again with fresh settings
                    client.set_settings({})
                    client.init()
                    client.login(username, password)
                    client.dump_settings(session_file)
            except json.JSONDecodeError:
                print(f"[{get_now()}] Session file is corrupted, deleting and re-logging in...")
                if os.path.exists(session_file):
                    os.remove(session_file)
                # Try logging in with fresh settings
                client.set_settings({})
                client.init()
                client.login(username, password)
                client.dump_settings(session_file)
        else:
            print(f"[{get_now()}] No session file found, logging in...")
            # Initialize fresh settings
            client.set_settings({})
            client.init()
            client.login(username, password)
            client.dump_settings(session_file)
            
        print(f"[{get_now()}] Successfully authenticated!")
    except Exception as e:
        print(f"[{get_now()}] Authentication error: {e}")
        print(f"[{get_now()}] Please check your credentials and try again.")
        sys.exit(1)


def load_seen_messages(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return set(json.load(f))
    else:
        return set()


def save_seen_messages(file, messages):
    with open(file, "w") as f:
        json.dump(list(messages), f)


def get_now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def sleep_countdown():
    # check for new messages every random seconds
    # sleep_time = random.randint(30 * 60, 60 * 60)
    sleep_time = 0;
    print(f"[{get_now()}] Timeout duration: {sleep_time} seconds.")

    for remaining_time in range(sleep_time, 0, -1):
        sys.stdout.write(f"\r[{get_now()}] Time remaining: {remaining_time} second(s).")
        sys.stdout.flush()
        time.sleep(1)

    sys.stdout.write("\n")


def main():
    # Initialize client with mobile user agent
    cl = Client()
    cl.delay_range = [3, 6]  # Increase delay between requests
    cl.set_user_agent("Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 231.1.0.18.118 (iPhone13,4; iOS 15_5; en_US; en-US; scale=3.00; 1284x2778; 357099330)")

    session_file = "session.json"
    seen_messages_file = "seen_messages.json"
    authenticate(cl, session_file)
    user_id = cl.user_id_from_username(username)
    print(f"[{get_now()}] Logged in as user ID {user_id}")

    if login_only:
        print(f"[{get_now()}] LOGIN_ONLY is set to true, the script ends here")
        return

    seen_message_ids = load_seen_messages(seen_messages_file)
    print(f"[{get_now()}] Loaded seen messages.")

    while True:
        
        try:
            # Approve pending message requests inside the loop
            pending_threads = cl.direct_pending_inbox()
            for thread in pending_threads:
                cl.direct_answer(thread.id, "yo, this is a 1 time message to approve your dm request :0 send a reel to get a clapback.")
                print(f"Approved thread: {thread.id}")

            print("All pending message requests approved.")
            
            threads = cl.direct_threads()
            print(f"[{get_now()}] Retrieved direct threads.")
            time.sleep(random.uniform(2, 4))  # Add delay between API calls

            for thread in threads:
                thread_id = thread.id
                messages = cl.direct_messages(thread_id)
                print(f"[{get_now()}] Retrieved messages.")
                time.sleep(random.uniform(2, 4))  # Add delay between API calls

                for message in messages:
                    if message.id not in seen_message_ids:
                        match message.item_type:
                            case "clip":
                                print(f"[{get_now()}] Processing reel {message.clip.pk}")
                                try:
                                    # Get reel comments
                                    comments = get_reel_comments(cl, message.clip.pk)
                                    time.sleep(random.uniform(2, 4))  # Add delay between API calls
                                    
                                    reel_description = message.clip.caption_text if hasattr(message.clip, 'caption_text') else ""
                                    
                                    # Generate and send clapback
                                    clapback = generate_clapback(comments, reel_description)
                                    send_clapback(cl, thread_id, clapback)
                                    time.sleep(random.uniform(2, 4))  # Add delay between API calls
                                except Exception as e:
                                    print(f"Error processing reel: {e}")
                            case "xma_story_share":
                                print(f"[{get_now()}] New story video in thread {thread_id}: {message.id}")
                            case _:
                                print(f"[{get_now()}] New message in thread {thread_id}: {message.text}")
                        seen_message_ids.add(message.id)
                        save_seen_messages(seen_messages_file, seen_message_ids)

        except Exception as e:
            print(f"[{get_now()}] An exception occurred: {e}")
            print(f"[{get_now()}] Deleting the session file and restarting the script.")
            if os.path.exists(session_file):
                os.remove(session_file)
            sleep_countdown()
            print(f"[{get_now()}] Restarting the script now.")
            os.execv(sys.executable, ["python"] + sys.argv)

        sleep_countdown()

if __name__ == "__main__":
    main()
