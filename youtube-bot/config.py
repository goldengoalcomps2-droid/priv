"""Default configuration for the YouTube automation bot."""

# Browser settings
BROWSER_TYPE = "chromium"  # "chromium", "firefox", or "webkit"
HEADLESS = False  # Must be False to watch videos
SLOW_MO = 50  # Milliseconds between actions for stability

# Video playback
DEFAULT_WATCH_DURATION = 90  # seconds (1 minute 30 seconds)
MAX_VIDEOS_PER_SESSION = 20
AD_CHECK_INTERVAL = 2  # seconds between ad-skip checks

# Timeouts
PAGE_LOAD_TIMEOUT = 30000  # ms
ELEMENT_TIMEOUT = 10000  # ms
NAVIGATION_TIMEOUT = 30000  # ms

# Selectors (YouTube DOM selectors)
SELECTORS = {
    "search_input": 'input#search, input[name="search_query"], ytd-searchbox input',
    "search_button": 'button#search-icon-legacy, #search-icon-legacy',
    "video_thumbnail": 'ytd-video-renderer a#video-title',
    "channel_link": 'ytd-channel-renderer a.channel-link',
    "channel_name_search": 'ytd-channel-renderer #channel-title',
    "channel_videos_tab": 'yt-tab-shape[tab-title="Videos"]',
    "channel_video_items": 'ytd-rich-item-renderer a#video-title-link',
    "like_button": 'like-button-view-model button',
    "skip_ad_button": 'button.ytp-skip-ad-button, button.ytp-ad-skip-button, button.ytp-ad-skip-button-modern',
    "ad_overlay": '.ytp-ad-player-overlay, .video-ads.ytp-ad-module',
    "ad_text": '.ytp-ad-text, .ytp-ad-preview-text',
    "video_player": 'video.html5-main-video',
    "comments_section": 'ytd-comments#comments',
    "comment_content": '#content-text',
    "comment_author": '#author-text',
    "mute_button": 'button.ytp-mute-button',
    "play_button": 'button.ytp-play-button',
    "cookie_accept": 'button[aria-label="Accept all"], button[aria-label="Accept the use of cookies and other data for the purposes described"], [aria-label="Reject all"], form[action*="consent"] button',
    "dismiss_signin": 'button[aria-label="No thanks"], tp-yt-paper-button[aria-label="No thanks"], button.yt-spec-button-shape-next[aria-label="No thanks"], #dismiss-button, .style-scope.yt-button-renderer[aria-label="Dismiss"]',
}
