# Sidebar UI Enhancements - Lead Hunter Toolkit

## Overview
This document describes the enhanced plugin management panel and vertical preset selector interface for the Lead Hunter Toolkit Streamlit app.

## Implementation Status
✅ Enhanced sidebar code created in `sidebar_enhanced.py`
⏳ Ready to integrate into `app.py` (replace lines 275-471)

## Key Enhancements

### 1. Vertical Preset Selector (Enhanced)

#### Visual Improvements
- **Icons**: Each vertical has a dedicated emoji icon (🍽️ Restaurant, 🛍️ Retail, 💼 Professional Services)
- **Status Badge**: Clear visual indicator showing active vertical with icon
- **Improved Formatting**: Vertical names displayed with proper title case and icons in selector

#### New Features

##### A. Scoring Weight Comparisons
- **Visual Metrics**: Shows scoring weight differences vs defaults using `st.metric()`
- **Percentage Changes**: Displays percentage increase/decrease for each weight
- **3-Column Layout**: Compact display of all scoring weights
- **Color Coding**: Positive changes in green, negative in red

Example display:
```
📊 Scoring Weight Adjustments:
┌──────────┬──────────┬──────────┐
│ Email    │ Phone    │ Social   │
│ 2.5      │ 2.0      │ 1.0      │
│ +25%     │ +100%    │ +100%    │
└──────────┴──────────┴──────────┘
```

##### B. Vertical Settings Expander
When a vertical is active, shows detailed configuration:

1. **Description**: Brief vertical overview
2. **Scoring Adjustments**: All weight changes with metrics
3. **Focus Areas**: Top 5 areas of emphasis (with "...and X more" for additional)
4. **Common Issues**: Top 3 typical problems this vertical addresses
5. **Value Propositions**: Top 3 value props for outreach

##### C. Action Buttons
- **Reset to Defaults**: Clear active vertical and restore default weights
- **Score Preview**: Info button explaining how to see scoring changes
- **Apply Button**: Now styled as primary button for better visibility

##### D. User Feedback
- **Toast Notification**: Reminds users to re-score leads after applying vertical
- **Success Messages**: Clear feedback on all actions
- **Info Badges**: Visual status indicators

### 2. Plugin Management Panel (Enhanced)

#### Visual Improvements
- **Success Badge**: Shows "✓ X plugin(s) active" instead of generic info
- **Plugin Cards**: Each plugin now has a dedicated expander card
- **Icon Prefixes**: 🔧 for plugins, 🔗 for hooks, 👤 for authors

#### New Features

##### A. Plugin Cards with Toggles
Each plugin card shows:
- **Header**: Plugin name + version with toggle switch
- **Description**: Plugin purpose and functionality
- **Author**: Plugin creator information
- **Hook Points**: List of registered hooks in code format
- **Status Metrics**: Shows "✅ Active" or "⏸️ Plugin disabled"
- **File Location**: Display plugin filename

##### B. Enable/Disable Toggle
- **Per-Plugin Control**: Toggle individual plugins on/off
- **Session Persistence**: State maintained in `st.session_state.plugin_enabled`
- **Visual Feedback**: Status metric changes based on enabled state

##### C. Configuration Button (Placeholder)
- **Future-Proof**: Configure button prepared for plugin-specific settings
- **Disabled State**: Currently disabled with "coming soon" message
- **Full Width**: Uses `use_container_width=True` for better UX

##### D. Reload with Confirmation
- **Two-Click Reload**: Prevents accidental plugin reloads
- **Warning Message**: Shows "⚠️ Click again to confirm reload" on first click
- **State Management**: Uses `st.session_state.confirm_reload_plugins`

##### E. Plugin Documentation Link
- **Plugin Docs Button**: Links to plugin development guide
- **Helper Text**: Shows info message about README location
- **Side-by-Side Layout**: Reload and Docs buttons in 2-column layout

### 3. LLM Settings (Enhanced)

#### New Features

##### A. LLM Timeout Configuration
- **New Setting**: `llm_timeout` (10-300 seconds)
- **Helpful Tooltip**: Explains purpose for long-running LLM calls
- **Default**: 60 seconds

##### B. Test Connection Button
- **Live Testing**: Verify LLM endpoint accessibility
- **Simple Test**: Sends "Reply with OK" prompt
- **Error Handling**: Catches and displays connection errors
- **Spinner**: Shows "Testing connection..." during request
- **Validation**: Warns if base URL not provided

### 4. General UI Improvements

#### Better Spacing and Layout
- **Consistent Columns**: 2-column and 3-column layouts for compact display
- **Proper Dividers**: `st.divider()` between major sections
- **Caption Hierarchy**: Uses `st.caption()` for secondary text

#### Enhanced Feedback
- **Toast Notifications**: Important reminders (re-score after vertical change)
- **Success Messages**: All actions provide clear feedback
- **Info Messages**: Helpful hints throughout

#### Visual Icons
- 🎯 Vertical Presets
- 🔌 Plugins
- 🔧 Plugin cards
- 🔗 Hook points
- 👤 Author
- 📁 File location
- 📊 Scoring weights
- 🎯 Focus areas
- ⚠️ Issues
- 💰 Value props
- ✅ Active status
- ⏸️ Disabled status

## Integration Instructions

### Option 1: Manual Integration
1. Open `app.py`
2. Locate lines 275-471 (entire sidebar section)
3. Replace with content from `sidebar_enhanced.py`
4. Test thoroughly

### Option 2: Automated (Recommended)
```python
# In app.py, replace the sidebar section with:
from sidebar_enhanced import sidebar_content
sidebar_content(st, load_settings, save_settings, ConfigLoader, load_plugins, Path)
```

## Technical Details

### Dependencies
- All existing dependencies (no new requirements)
- Uses `config.loader.ConfigLoader` for vertical management
- Uses `plugins.loader.load_plugins` for plugin system

### Session State Keys
- `plugins`: List of loaded plugin metadata
- `plugins_loaded`: Boolean flag
- `plugin_enabled`: Dict mapping plugin names to enabled state
- `confirm_reload_plugins`: Boolean for reload confirmation
- `active_vertical`: Active vertical preset name (stored in settings.json)

### Settings Keys (New/Modified)
- `llm_timeout`: LLM request timeout in seconds
- `active_vertical`: Currently active vertical preset name

## Testing Checklist

- [ ] Vertical preset selector shows icons
- [ ] Active vertical displays with correct icon and name
- [ ] Scoring weight metrics show correct differences
- [ ] Vertical settings expander shows all sections
- [ ] Reset to Defaults button works
- [ ] Apply button triggers re-score notification
- [ ] Plugin cards display correctly
- [ ] Plugin toggles persist across reloads
- [ ] Plugin status metrics update correctly
- [ ] Reload plugins requires confirmation
- [ ] Plugin docs button shows helpful info
- [ ] Test LLM Connection button works
- [ ] All tooltips display correctly
- [ ] Layout is responsive and clean

## Screenshots

### Vertical Preset Selector (Enhanced)
```
🎯 Vertical Presets
Industry-specific scoring and outreach optimization

🍽️ Active: Restaurant

[Select vertical ▼] [Apply]

🍽️ Restaurant Settings
  Description: Restaurant and food service businesses

  📊 Scoring Weight Adjustments:
  Email     Phone     Social
  2.5       2.0       1.0
  +25%      +100%     +100%

  🎯 Focus Areas:
  ✓ Online reservations
  ✓ Google My Business
  ✓ Menu visibility
  ...and 3 more

  ⚠️ Common Issues:
  • No online reservation system
  • Menu not searchable
  • Poor Google Business profile

  💰 Value Propositions:
  • 20-30% more online reservations
  • Top 3 Google Maps rankings
  • Instagram-ready menu photos

  [🔄 Reset to Defaults] [📊 Score Preview]
```

### Plugin Management Panel (Enhanced)
```
🔌 Plugins
Extend functionality with custom plugins

✓ 2 plugin(s) active

🔧 example_plugin v1.0.0
  Data enrichment and scoring enhancements

  👤 Author: Plugin Developer

  🔗 Hook Points:
  • `after_extract`
  • `before_score`

  Status: ✅ Active
  📁 example_plugin.py

  [⚙️ Configure]

[🔄 Reload Plugins] [ℹ️ Plugin Docs]
```

## Future Enhancements

### Vertical Preset Selector
1. **Preview Mode**: Show sample lead scoring before/after vertical
2. **Custom Verticals**: UI for creating new vertical presets
3. **Import/Export**: Share vertical configs as YAML
4. **Vertical Comparison**: Side-by-side vertical comparison

### Plugin Management
1. **Plugin Marketplace**: Browse and install plugins
2. **Plugin Settings UI**: Dynamic settings forms per plugin
3. **Plugin Statistics**: Track call counts and execution times
4. **Plugin Dependencies**: Show plugin dependency graphs
5. **Hot Reload**: Reload individual plugins without restart
6. **Plugin Logs**: View plugin-specific log messages

### LLM Settings
1. **Model Presets**: Quick presets for common models
2. **Model Selector**: Dropdown with available models from endpoint
3. **Vision Indicator**: Badge showing if model supports vision
4. **Cost Estimator**: Show approximate cost per request
5. **Performance Metrics**: Track LLM response times

## Notes

- All emoji icons are optional and can be removed if not desired
- Plugin enable/disable is UI-only; actual hook filtering needs implementation
- Test LLM Connection is basic; can be enhanced with more thorough testing
- Vertical score preview is placeholder; full implementation requires scoring simulation

## Support

For questions or issues with the enhanced sidebar:
1. Check this documentation first
2. Review `sidebar_enhanced.py` for implementation details
3. Test with different verticals to ensure compatibility
4. Verify plugin metadata structure matches expected format
