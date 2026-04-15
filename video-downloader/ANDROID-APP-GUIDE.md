# Getting SnapVid on Android - Complete Guide

Your video downloader is now a **Progressive Web App (PWA)**. This means users can install it on their phone like a native app - no Play Store required.

You have TWO ways to distribute it:

---

## METHOD 1: PWA Install (Available Now - No Setup Required)

Users visit your website on their phone and install it in 2 taps.

### What Users See on Android:
1. Open Chrome, visit your site (e.g. `priv-i53i.onrender.com`)
2. Chrome shows an "Install App" banner, OR they tap Menu > "Install app"
3. App icon appears on their home screen
4. Opens full-screen, no browser UI - looks and feels like a native app

### What Users See on iPhone:
1. Open Safari, visit your site
2. Tap Share button > "Add to Home Screen"
3. App icon appears on home screen
4. Opens full-screen

### Bonus Features Built In:
- **Offline support** - homepage loads even without internet
- **Share target** - users can share a YouTube/TikTok URL from any app directly to SnapVid to download it
- **App shortcuts** - long-press the icon for "Paste & Download"
- **Auto-fill URL** - if a URL is shared to the app, it automatically starts downloading

### Your Action: **None!** This is already live. Just share your site URL.

---

## METHOD 2: Google Play Store (Optional - For Trust & Discovery)

Publishing on Play Store gives you:
- Higher trust (users trust apps from Play Store)
- Discoverability (Play Store search brings organic traffic)
- Professional appearance
- Better for ad revenue (higher click-through rates)

### Cost:
- **One-time $25** Google Play Developer registration fee
- **Free** to publish

### How It Works: Trusted Web Activity (TWA)
A TWA is a thin Android app that wraps your website. Google's official tool `Bubblewrap` handles all the hard work.

### Step-by-Step Publishing Guide

#### Step 1: Prepare Your Site (Already Done)
- HTTPS enabled (Render provides this automatically)
- PWA manifest (already created at `/static/manifest.json`)
- Service worker (already created at `/static/sw.js`)
- Icons (already generated)

#### Step 2: Install Bubblewrap
Run on your laptop:
```bash
# Install Node.js first if you don't have it (nodejs.org)
npm install -g @bubblewrap/cli

# Install JDK and Android SDK (Bubblewrap will prompt you)
bubblewrap doctor
```

#### Step 3: Initialize Your TWA Project
```bash
# Create a new folder for the TWA
mkdir snapvid-twa
cd snapvid-twa

# Initialize from your PWA
bubblewrap init --manifest https://YOUR-RENDER-URL.onrender.com/static/manifest.json
```

Bubblewrap will ask you questions:
- **Domain:** your-render-url.onrender.com (or custom domain)
- **Application name:** SnapVid
- **Short name:** SnapVid
- **Application ID:** com.snapvid.app (reverse domain)
- **Display mode:** standalone
- **Orientation:** portrait
- **Status bar colour:** #0a0a0a
- **Splash screen colour:** #0a0a0a

#### Step 4: Build the APK / AAB
```bash
bubblewrap build
```

This creates:
- `app-release-signed.apk` - for testing on your phone
- `app-release-bundle.aab` - for uploading to Play Store

#### Step 5: Test on Your Phone
```bash
# Install the APK on your connected Android device
bubblewrap install
```

Or transfer `app-release-signed.apk` to your phone and install it manually.

#### Step 6: Verify Digital Asset Links
Bubblewrap will show a file called `assetlinks.json`. You need to host this at:
```
https://YOUR-URL.onrender.com/.well-known/assetlinks.json
```

This proves you own both the website and the app (prevents someone else from wrapping your site).

To add it to your Flask app, create the file and the Flask route:
```python
@app.route('/.well-known/assetlinks.json')
def asset_links():
    return send_from_directory('static', 'assetlinks.json')
```

#### Step 7: Create Google Play Developer Account
1. Go to: https://play.google.com/console
2. Pay the one-time $25 registration fee
3. Fill out developer profile

#### Step 8: Submit Your App
1. Click "Create app" in Play Console
2. Fill in:
   - App name: SnapVid
   - Default language: English
   - App or game: App
   - Free or paid: Free
3. Upload `app-release-bundle.aab`
4. Add screenshots (take 4-8 screenshots of your app running)
5. Add app icon (use `icon-512.png` from your static/icons folder)
6. Write description (I'll generate one below)
7. Complete content rating questionnaire
8. Submit for review

Review takes **1-7 days** typically. Once approved, your app is live on Play Store worldwide.

---

## Ready-to-Use Play Store Listing

### Short Description (80 chars max)
```
Download videos from YouTube, TikTok, Instagram & 1000+ sites. Free & fast.
```

### Full Description
```
SnapVid is the fastest way to download videos from any website. Works with YouTube, TikTok, Instagram, Twitter, Facebook, Vimeo, Reddit, and 1000+ more sites.

KEY FEATURES:
• Download any video in one tap
• Choose quality: 1080p HD, 720p, 480p, or Audio Only (MP3)
• Works with 1000+ websites
• No signup, no account required
• 100% free
• No watermarks
• Lightning fast downloads
• Share videos directly from any app

HOW TO USE:
1. Copy the video URL from your browser or any app
2. Open SnapVid and paste the URL
3. Select quality and hit Download
4. Save the video to your phone

SUPPORTED SITES:
YouTube, TikTok, Instagram, Twitter/X, Facebook, Reddit, Vimeo, Twitch, Dailymotion, SoundCloud, Tumblr, and many more.

PRIVACY FIRST:
We don't store your downloads. Files are deleted from our servers within 10 minutes after your download.

Note: Please respect copyright. Only download videos you have permission to save.
```

### Category
- **Primary:** Video Players & Editors
- **Secondary:** Tools

### Tags
`video downloader, youtube downloader, tiktok downloader, instagram video, mp4 downloader, mp3 downloader, video grabber, save video, free video download`

---

## Monetisation Inside the App

All your existing web monetisation works automatically in the TWA:
- Google AdSense ads
- NordVPN affiliate links
- Any future banners/promos

Plus you can add:
- **Google AdMob** (native Android ads) - higher CPM than AdSense
- **In-app purchases** - premium tier ($2.99/month for 4K, no ads, batch downloads)
- **Rewarded ads** - "Watch an ad to unlock 4K" = premium ad revenue

---

## iOS App (iPhone)

Apple is stricter - they don't allow TWAs. Options for iPhone:
1. **PWA via Safari "Add to Home Screen"** - works, already set up. Users just visit and install.
2. **Native iOS app** - would require Swift/SwiftUI development + $99/year Apple Developer fee
3. **Capacitor / Cordova wrapper** - similar to TWA for iOS, but Apple sometimes rejects these

**My recommendation:** Start with Android (Play Store). iOS users can still install via Safari's "Add to Home Screen" - it works almost identically to a native app.

---

## Summary

| Option | Cost | Effort | Timeline |
|--------|------|--------|----------|
| **PWA Install (both iOS & Android)** | £0 | Zero - already done | Live now |
| **Google Play Store (TWA)** | £20 one-time | 2-4 hours setup | 1-7 day review |
| **Apple App Store** | £80/year | 40+ hours development | 1-14 day review |

Start with the PWA. When you're getting 500+ daily visitors, invest in Play Store publishing.
