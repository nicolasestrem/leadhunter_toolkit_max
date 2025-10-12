# Visual Guide: Enhanced Sidebar UI

## 📸 Complete Walkthrough

This guide shows exactly what users will see and interact with in the enhanced sidebar.

---

## Section 1: Standard Settings (Unchanged)

```
┌─────────────────────────────────────────────────┐
│ Settings                                        │
├─────────────────────────────────────────────────┤
│                                                 │
│ Search engine:  [google ▼]                      │
│                                                 │
│ Project name:   [default________________]       │
│ Country code:   [fr_____________________]       │
│ Language:       [fr-FR__________________]       │
│ City focus:     [Toulouse_______________]       │
│ Radius km:      [50]                            │
│                                                 │
│ Max sites to scan (per query)                   │
│ ├─────●────────────┤ 25                         │
│                                                 │
│ Fetch timeout seconds                           │
│ ├──●───────────────┤ 15                         │
│                                                 │
│ Concurrency                                     │
│ ├────────●─────────┤ 8                          │
│                                                 │
│ [✓] Deep crawl contact/about pages              │
│                                                 │
│ Max pages per site                              │
│ ├──●───────────────┤ 5                          │
│                                                 │
│ [✓] Extract emails                              │
│ [✓] Extract phones                              │
│ [✓] Extract social links                        │
│                                                 │
│ Google Places API key: [******************]     │
│ Places region:         [FR____________]         │
│ Places language:       [fr____________]         │
│                                                 │
│ Google CSE API key:    [******************]     │
│ Google CSE cx:         [___________________]    │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## Section 2: LLM Settings (Enhanced)

```
┌─────────────────────────────────────────────────┐
│ LLM                                             │
├─────────────────────────────────────────────────┤
│                                                 │
│ LLM base URL:  [https://lm.leophir.com/____]   │
│ LLM API key:   [**************************]    │
│ LLM model:     [openai/gpt-oss-20b_______]     │
│                                                 │
│ ▼ Advanced LLM Settings                         │
│   │                                             │
│   │ Temperature                                 │
│   │ ├───●──────────┤ 0.2                        │
│   │ ℹ Controls randomness: 0.0 = determin...   │
│   │                                             │
│   │ Max tokens (0 = unlimited)                  │
│   │ [2048_____]                                 │
│   │ ℹ Maximum tokens in LLM response...         │
│   │                                             │
│   │ LLM timeout (seconds) ⭐ NEW                │
│   │ [60______]                                  │
│   │ ℹ Maximum time to wait for LLM response    │
│   │                                             │
│   │ ┌─────────────────────────────────┐        │
│   │ │ 🔌 Test LLM Connection          │        │
│   │ └─────────────────────────────────┘        │
│   │                                             │
│   │ (After clicking test button)                │
│   │ ⏳ Testing connection...                    │
│   │ ✅ LLM connection successful!               │
│   └─────────────────────────────────────        │
│                                                 │
│ ┌───────────────────────────────────────────┐  │
│ │        💾 Save settings                   │  │
│ └───────────────────────────────────────────┘  │
│                                                 │
└─────────────────────────────────────────────────┘
```

**New in LLM Settings:**
- ⭐ LLM timeout input
- ⭐ Test Connection button
- ⭐ Live connection testing with spinner
- ⭐ Clear success/error feedback
- ⭐ Full-width save button

---

## Section 3: Vertical Presets (Enhanced) 🎯

### 3a. No Active Vertical

```
┌─────────────────────────────────────────────────┐
│ 🎯 Vertical Presets                             │
├─────────────────────────────────────────────────┤
│ Industry-specific scoring and outreach optim... │
│                                                 │
│ ⚙️ No vertical preset active (using defaults)  │
│                                                 │
│ Select vertical:                                │
│ [⚙️ Default Settings ▼]          [Apply ⚡]     │
│                                                 │
│   Options in dropdown:                          │
│   • ⚙️ Default Settings                         │
│   • 🍽️ Restaurant                               │
│   • 🛍️ Retail                                   │
│   • 💼 Professional Services                    │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 3b. Restaurant Vertical Active

```
┌─────────────────────────────────────────────────┐
│ 🎯 Vertical Presets                             │
├─────────────────────────────────────────────────┤
│ Industry-specific scoring and outreach optim... │
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ 🍽️ Active: Restaurant                       │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Select vertical:                                │
│ [🍽️ Restaurant ▼]                [Apply ⚡]     │
│                                                 │
│ ▼ 🍽️ Restaurant Settings                        │
│   │                                             │
│   │ Description: Restaurant and food service... │
│   │                                             │
│   │ 📊 Scoring Weight Adjustments:              │
│   │ ┌────────┬────────┬────────┐               │
│   │ │ Email  │ Phone  │ Social │               │
│   │ │  2.5   │  2.0   │  1.0   │               │
│   │ │ +25%⬆ │ +100%⬆│ +100%⬆│               │
│   │ ├────────┼────────┼────────┤               │
│   │ │Contact │ City   │ Google │               │
│   │ │  1.5   │  2.0   │  2.0   │               │
│   │ │ +50%⬆ │ +33%⬆ │  N/A   │               │
│   │ └────────┴────────┴────────┘               │
│   │                                             │
│   │ 🎯 Focus Areas:                             │
│   │ ✓ Online reservations                       │
│   │ ✓ Google My Business                        │
│   │ ✓ Menu visibility                           │
│   │ ✓ Review management                         │
│   │ ✓ Local SEO                                 │
│   │ ...and 1 more                               │
│   │                                             │
│   │ ⚠️ Common Issues to Address:                │
│   │ • No online reservation system              │
│   │ • Menu not searchable                       │
│   │ • Poor Google Business profile              │
│   │                                             │
│   │ 💰 Value Propositions:                      │
│   │ • 20-30% more online reservations           │
│   │ • Top 3 Google Maps rankings                │
│   │ • Instagram-ready menu photos               │
│   │                                             │
│   │ ────────────────────────────────────        │
│   │                                             │
│   │ ┌──────────────┐ ┌──────────────┐          │
│   │ │🔄 Reset to   │ │📊 Score      │          │
│   │ │   Defaults   │ │   Preview    │          │
│   │ └──────────────┘ └──────────────┘          │
│   │                                             │
│   └─────────────────────────────────────        │
│                                                 │
└─────────────────────────────────────────────────┘

When user clicks "Apply" button:
┌────────────────────────────────────┐
│ ✅ Applied vertical: restaurant    │
└────────────────────────────────────┘

┌────────────────────────────────────┐
│ 🔄 Toast: ⚠️ Re-score leads to     │
│          apply new weights         │
└────────────────────────────────────┘
```

### 3c. Retail Vertical Active

```
┌─────────────────────────────────────────────────┐
│ 🎯 Vertical Presets                             │
├─────────────────────────────────────────────────┤
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ 🛍️ Active: Retail                           │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ [🛍️ Retail ▼]                    [Apply ⚡]     │
│                                                 │
│ ▼ 🛍️ Retail Settings                            │
│   │ (Similar structure to Restaurant)           │
│   │ Different weights, focus areas, etc.        │
│   └─────────────────────────────────────        │
│                                                 │
└─────────────────────────────────────────────────┘
```

**New in Vertical Presets:**
- ⭐ Visual icons (🍽️ 🛍️ 💼)
- ⭐ Active status badge with icon
- ⭐ Icons in dropdown selector
- ⭐ Metric cards with percentage deltas
- ⭐ 3-column scoring weight layout
- ⭐ Focus areas list (top 5 + more)
- ⭐ Common issues (top 3)
- ⭐ Value propositions (top 3)
- ⭐ Reset and Preview buttons
- ⭐ Toast notification on apply
- ⭐ Primary button styling

---

## Section 4: Plugins (Enhanced) 🔌

### 4a. No Plugins Loaded

```
┌─────────────────────────────────────────────────┐
│ 🔌 Plugins                                      │
├─────────────────────────────────────────────────┤
│ Extend functionality with custom plugins        │
│                                                 │
│ No plugins loaded                               │
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ ℹ 💡 Add .py files to the plugins/          │ │
│ │    directory to extend functionality        │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ ┌──────────────┐  ┌──────────────┐             │
│ │ 🔄 Reload    │  │ ℹ️ Plugin    │             │
│ │   Plugins    │  │   Docs       │             │
│ └──────────────┘  └──────────────┘             │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 4b. Two Plugins Loaded (Both Enabled)

```
┌─────────────────────────────────────────────────┐
│ 🔌 Plugins                                      │
├─────────────────────────────────────────────────┤
│ Extend functionality with custom plugins        │
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ ✅ 2 plugin(s) active                       │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ ▼ 🔧 example_plugin v1.0.0                      │
│   │                                             │
│   │ Data enrichment and scoring...  [Enable ⚪]│
│   │                                             │
│   │ 👤 Author: Plugin Developer                │
│   │                                             │
│   │ 🔗 Hook Points:                             │
│   │ • `after_extract`                           │
│   │ • `before_score`                            │
│   │                                             │
│   │ Status: ✅ Active  📁 example_plugin.py     │
│   │         ▲ Ready                             │
│   │                                             │
│   │ ┌───────────────────────────────────────┐  │
│   │ │      ⚙️ Configure                     │  │
│   │ └───────────────────────────────────────┘  │
│   │ (Button is disabled - "coming soon")        │
│   │                                             │
│   └─────────────────────────────────────        │
│                                                 │
│ ▼ 🔧 analytics_plugin v0.5.0                    │
│   │                                             │
│   │ Track and analyze lead...       [Enable ⚪]│
│   │                                             │
│   │ 👤 Author: Analytics Team                  │
│   │                                             │
│   │ 🔗 Hook Points:                             │
│   │ • `after_classify`                          │
│   │ • `before_export`                           │
│   │                                             │
│   │ Status: ✅ Active  📁 analytics_plugin.py   │
│   │         ▲ Ready                             │
│   │                                             │
│   │ ┌───────────────────────────────────────┐  │
│   │ │      ⚙️ Configure                     │  │
│   │ └───────────────────────────────────────┘  │
│   │                                             │
│   └─────────────────────────────────────        │
│                                                 │
│ ┌──────────────┐  ┌──────────────┐             │
│ │ 🔄 Reload    │  │ ℹ️ Plugin    │             │
│ │   Plugins    │  │   Docs       │             │
│ └──────────────┘  └──────────────┘             │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 4c. Plugin Disabled

```
┌─────────────────────────────────────────────────┐
│ ▼ 🔧 example_plugin v1.0.0                      │
│   │                                             │
│   │ Data enrichment and scoring...  [Enable ⚫]│
│   │                                    (OFF)    │
│   │ 👤 Author: Plugin Developer                │
│   │                                             │
│   │ 🔗 Hook Points:                             │
│   │ • `after_extract`                           │
│   │ • `before_score`                            │
│   │                                             │
│   │ ┌─────────────────────────────────────────┐ │
│   │ │ ⚠️ ⏸️ Plugin disabled                    │ │
│   │ └─────────────────────────────────────────┘ │
│   │                                             │
│   │ ┌───────────────────────────────────────┐  │
│   │ │      ⚙️ Configure                     │  │
│   │ └───────────────────────────────────────┘  │
│   │                                             │
│   └─────────────────────────────────────        │
└─────────────────────────────────────────────────┘
```

### 4d. Reload Confirmation Flow

```
First click:
┌──────────────┐  ┌──────────────┐
│ 🔄 Reload    │  │ ℹ️ Plugin    │
│   Plugins    │  │   Docs       │
└──────────────┘  └──────────────┘

After first click:
┌────────────────────────────────────┐
│ ⚠️ ⚠️ Click again to confirm reload│
└────────────────────────────────────┘

Second click:
┌────────────────────────────────────┐
│ ✅ Reloaded 2 plugins              │
└────────────────────────────────────┘
(Page reloads)
```

### 4e. Plugin Docs Click

```
After clicking "Plugin Docs":
┌────────────────────────────────────┐
│ ℹ️ 📚 See plugins/README.md for    │
│    plugin development guide        │
└────────────────────────────────────┘
```

**New in Plugins:**
- ⭐ Success badge (not info badge)
- ⭐ Individual plugin cards
- ⭐ Enable/disable toggle per plugin
- ⭐ Status metrics (Active/Disabled)
- ⭐ Author display with icon
- ⭐ Hook points in code format
- ⭐ File location display
- ⭐ Configure button (prepared)
- ⭐ Two-click reload confirmation
- ⭐ Plugin docs button
- ⭐ Better empty state message

---

## Section 5: Remaining Sections (Unchanged)

```
┌─────────────────────────────────────────────────┐
│ Presets                                         │
├─────────────────────────────────────────────────┤
│ Save/load configurations per niche or location  │
│                                                 │
│ Load preset:        [_______________▼]          │
│                                     [Load]      │
│                                                 │
│ Save as preset:     [berlin_plumbers___]        │
│ [Save preset]                                   │
│                                                 │
│ [Delete preset]                                 │
│                                                 │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Cache Management                                │
├─────────────────────────────────────────────────┤
│ Manage HTTP response cache                      │
│                                                 │
│ Cache Files:  150 files                         │
│ Cache Size:   45.3 MB                           │
│ Max size: 500 MB • Max age: 30 days             │
│                                                 │
│ [Cleanup Expired]  [Clear All Cache]            │
│                                                 │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Export current table                            │
│ (Empty placeholder)                             │
└─────────────────────────────────────────────────┘
```

---

## 📱 Responsive Behavior

### Desktop (Wide Sidebar)
- All 3-column layouts display fully
- Metric cards side by side
- Full button text visible
- All icons display

### Tablet (Medium Sidebar)
- 3-column layouts may wrap
- Metric cards still visible
- Button text may truncate
- Icons remain visible

### Mobile (Narrow Sidebar)
- Single column layout
- Metrics stack vertically
- Buttons use container width
- Icons help save space

---

## 🎨 Color Scheme

### Status Colors
- **Success**: Green (active plugins, applied vertical)
- **Warning**: Yellow/Orange (confirmations, warnings)
- **Info**: Blue (helpful information)
- **Error**: Red (connection failures)

### Delta Colors (Metrics)
- **Positive**: Green up arrow (⬆)
- **Negative**: Red down arrow (⬇)
- **Neutral**: Gray dash (-)

### UI Elements
- **Primary Button**: Blue/Purple
- **Secondary Button**: Gray
- **Toggle On**: Green/Blue
- **Toggle Off**: Gray

---

## 🔔 Notification Types

### Toast Notifications
```
┌────────────────────────────────┐
│ 🔄 ⚠️ Re-score leads to apply  │
│         new weights            │
└────────────────────────────────┘
(Appears top-right, auto-dismisses after 3s)
```

### Success Messages
```
┌────────────────────────────────┐
│ ✅ Applied vertical: restaurant│
└────────────────────────────────┘
```

### Warning Messages
```
┌────────────────────────────────┐
│ ⚠️ Click again to confirm reload│
└────────────────────────────────┘
```

### Info Messages
```
┌────────────────────────────────┐
│ ℹ️ 💡 Apply vertical and re-score│
│    leads in the Leads tab to  │
│    see changes                 │
└────────────────────────────────┘
```

### Error Messages
```
┌────────────────────────────────┐
│ ❌ Connection failed: [error]  │
└────────────────────────────────┘
```

---

## 📊 Data Flow Diagrams

### Vertical Preset Application

```
User selects vertical
        ↓
Clicks "Apply"
        ↓
Update settings.json
        ↓
Reload config loader
        ↓
Show success message
        ↓
Show toast notification
        ↓
Trigger app rerun
        ↓
New weights applied
```

### Plugin Toggle

```
User clicks toggle
        ↓
Update session_state
        ↓
UI updates immediately
        ↓
Plugin remains loaded
        ↓
(Future: filter hook calls)
```

### LLM Connection Test

```
User clicks "Test Connection"
        ↓
Show spinner
        ↓
Create test LLMClient
        ↓
Send "Reply with OK" prompt
        ↓
Wait for response (with timeout)
        ↓
Display success or error
```

---

## 🎭 User Interaction Examples

### Example 1: Switching Verticals

1. User sees "🍽️ Active: Restaurant"
2. Opens dropdown, sees icons for each vertical
3. Selects "🛍️ Retail"
4. Clicks "Apply ⚡" button
5. Sees "✅ Applied vertical: retail"
6. Sees toast: "🔄 ⚠️ Re-score leads..."
7. Page refreshes
8. New weights are active

### Example 2: Testing LLM Connection

1. User enters LLM base URL
2. Expands "Advanced LLM Settings"
3. Clicks "🔌 Test LLM Connection"
4. Sees spinner: "⏳ Testing connection..."
5. (Success) Sees "✅ LLM connection successful!"
6. (Failure) Sees "❌ Connection failed: [error message]"

### Example 3: Disabling a Plugin

1. User expands plugin card
2. Sees toggle switch at "Enable ⚪"
3. Clicks toggle to disable
4. Toggle moves to "Enable ⚫"
5. Status changes to "⏸️ Plugin disabled"
6. Plugin remains in list but marked disabled

### Example 4: Reloading Plugins

1. User clicks "🔄 Reload Plugins"
2. Sees warning: "⚠️ Click again to confirm"
3. Clicks again
4. Sees success: "✅ Reloaded 2 plugins"
5. Page refreshes
6. Plugin list updates

---

## 💡 Pro Tips for Users

### Vertical Presets
- **Tip**: Re-score existing leads after changing vertical to apply new weights
- **Tip**: Use "Reset to Defaults" to clear vertical and restore original settings
- **Tip**: Check percentage deltas to understand weight impact

### Plugins
- **Tip**: Disable plugins you're not using to keep UI clean
- **Tip**: Check hook points to understand when plugins execute
- **Tip**: Two-click reload prevents accidental reloads

### LLM Settings
- **Tip**: Test connection before running long operations
- **Tip**: Increase timeout for large LLM requests
- **Tip**: Use lower temperature for deterministic results

---

**Last Updated**: 2025-10-12
**Version**: 1.0
**Status**: Complete ✅
