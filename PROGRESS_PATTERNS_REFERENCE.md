# Progress Indicator Patterns - Quick Reference

## When to Use Each Pattern

### 🔄 Multi-Phase Progress Bar
**Use when:** Operation has multiple distinct phases
**Duration:** >10 seconds
**Example:** Hunt tab crawling (search → crawl → extract → score)

```python
progress_bar = st.progress(0.0)
status_text = st.empty()

# Phase 1
status_text.text("🕷️ Crawling sites...")
progress_bar.progress(0.25)
do_crawl()

# Phase 2
status_text.text("📊 Extracting data...")
progress_bar.progress(0.5)
do_extract()

# Phase 3
status_text.text("⭐ Scoring leads...")
progress_bar.progress(0.75)
do_score()

# Complete
progress_bar.progress(1.0)
status_text.text("✓ Complete!")
st.success("✅ Processed X items")
st.toast("Done!", icon="✓")
```

---

### 🔁 Loop Progress with ETA
**Use when:** Iterating through items with LLM calls or slow operations
**Duration:** Variable, >30 seconds
**Example:** Lead classification

```python
progress_bar = st.progress(0.0)
status_text = st.empty()
start_time = datetime.datetime.now()

total = len(items)
for i, item in enumerate(items):
    # Calculate ETA after first item
    if i > 0:
        elapsed = (datetime.datetime.now() - start_time).total_seconds()
        avg_time = elapsed / i
        remaining = total - i
        est_remaining = avg_time * remaining
        eta_text = f" (ETA: {int(est_remaining)}s)"
    else:
        eta_text = ""

    # Update progress
    status_text.text(f"🔍 Processing {i+1}/{total}: {item.name[:40]}...{eta_text}")
    progress_bar.progress((i + 1) / total)

    # Do work
    process_item(item)

# Complete with statistics
status_text.text("✓ Complete!")
elapsed_total = (datetime.datetime.now() - start_time).total_seconds()
st.success(f"✅ Processed {total} items in {elapsed_total:.1f}s (avg {elapsed_total/total:.1f}s per item)")
st.toast(f"Processed {total} items", icon="✓")
```

---

### ⏳ Simple Spinner
**Use when:** Operation is fast (<5 seconds) or can't show granular progress
**Duration:** <5 seconds
**Example:** SERP tracking, simple API calls

```python
with st.spinner("🔍 Searching..."):
    result = do_work()

st.success(f"✅ Found {len(result)} items")
st.toast("Search complete!", icon="✓")
```

---

### 🔀 Conditional Progress
**Use when:** Some operations are optional or conditional
**Duration:** Variable
**Example:** SEO audit with optional LLM scoring

```python
progress_bar = st.progress(0.0)
status_text = st.empty()

status_text.text("📊 Basic analysis...")
progress_bar.progress(0.5)
basic_analysis()

if use_advanced:
    status_text.text("🤖 Running advanced analysis...")
    progress_bar.progress(0.85)
    advanced_analysis()

progress_bar.progress(1.0)
status_text.text("✓ Complete!")
st.success("✅ Analysis complete")
```

---

### 🎯 Batched Updates
**Use when:** Loop has many iterations, updating too frequently causes flicker
**Duration:** Variable
**Example:** Extracting 100+ pages

```python
progress_bar = st.progress(0.0)
status_text = st.empty()

total = len(items)
UPDATE_INTERVAL = 10  # Update every 10 items

for i, item in enumerate(items, 1):
    process_item(item)

    # Update only every 10 items or on last item
    if i % UPDATE_INTERVAL == 0 or i == total:
        status_text.text(f"📊 Processing {i}/{total}...")
        progress_bar.progress(i / total)

status_text.text("✓ Complete!")
st.success(f"✅ Processed {total} items")
```

---

### 🎨 Nested Operations
**Use when:** Inner operations are fast, outer loop is slow
**Duration:** Variable
**Example:** Fetching details for many places

```python
progress_bar = st.progress(0.0)
status_text = st.empty()

total = len(places)
for i, place in enumerate(places):
    # Outer progress
    if i % 5 == 0 or i == total - 1:
        status_text.text(f"📞 Fetching details {i+1}/{total}...")
        progress_bar.progress(0.3 + (i / total) * 0.6)

    # Inner operation (fast)
    details = fetch_details(place)
    process(details)

progress_bar.progress(1.0)
status_text.text("✓ Complete!")
```

---

## Icon Reference

### Operation Types
- 🕷️ Crawling/scraping
- 🔍 Searching
- 📊 Analyzing/extracting
- ⭐ Scoring/rating
- 🤖 LLM processing
- 📄 Converting/processing documents
- 💾 Saving files
- 🌐 Fetching pages
- 📞 API calls
- 🚀 Initializing
- ✍️ Generating content
- 🗺️ Parsing sitemaps
- 📡 Signal detection
- ⚠️ Issue detection
- ⚡ Quick wins

### Status Indicators
- ✓ Complete/success
- ❌ Failed/error
- ⏳ In progress
- 🎯 Target/goal
- 📁 File/directory
- 📈 Progress/metrics
- 🎉 Celebration

---

## Success Message Templates

### Simple Success
```python
st.success("✅ Operation complete")
```

### With Statistics
```python
st.success(f"✅ Processed {count} items with average score: {avg:.1f}")
```

### With Time
```python
st.success(f"✅ Completed in {elapsed:.1f}s (avg {elapsed/count:.1f}s per item)")
```

### With Multiple Metrics
```python
st.success(f"✅ Audited {len(audits)} pages, generated {len(wins)} quick wins")
```

### With Location
```python
st.success(f"✅ Extracted {len(pages)} pages from {domain}")
st.info(f"📁 Files saved in: `{output_dir}`")
```

---

## Toast Notification Guidelines

### When to Use
- Operation completion (always)
- Milestones reached (optional)
- Important status changes (optional)

### When NOT to Use
- Don't spam with too many toasts
- Don't use for intermediate steps
- Don't use for errors (use st.error)

### Examples
```python
# Simple completion
st.toast("Done!", icon="✓")

# With count
st.toast(f"Found {count} leads", icon="🔍")

# With specific icon
st.toast("Outreach variants ready!", icon="✉️")

# Score/metric
st.toast(f"SEO Score: {score}/100", icon="📊")
```

---

## Error Handling Pattern

```python
progress_bar = st.progress(0.0)
status_text = st.empty()

try:
    status_text.text("🚀 Starting operation...")
    progress_bar.progress(0.1)

    # ... do work ...

    progress_bar.progress(1.0)
    status_text.text("✓ Complete!")
    st.success("✅ Operation successful")
    st.toast("Done!", icon="✓")

except Exception as e:
    st.error(f"Operation failed: {str(e)}")
    status_text.text("❌ Operation failed")
    # Don't update progress bar, leave it at last position
```

---

## Progress Bar Best Practices

### Do's
✅ Start at 0.0 or 0.05 (5%)
✅ End at 1.0 (100%)
✅ Use meaningful intermediate values (0.25, 0.5, 0.75)
✅ Update smoothly through phases
✅ Leave at 100% on completion
✅ Clear status text on success

### Don'ts
❌ Don't jump backward
❌ Don't update too frequently (causes flicker)
❌ Don't leave stuck at incomplete value on error
❌ Don't use random values
❌ Don't hide progress bar on completion (let it stay at 100%)

---

## Status Text Best Practices

### Format
```
[Icon] [Action verb] [What] [Count/Details]... [Optional ETA]
```

### Examples
```python
"🕷️ Crawling site 5/25: example.com..."
"📊 Extracting page 50/120..."
"🤖 Analyzing content... (ETA: 15s)"
"💾 Saving 25 files..."
"✓ Complete! Found 120 pages"
```

### Do's
✅ Use present continuous tense (-ing)
✅ Include counts when possible (X/Y)
✅ Truncate long names ([:40])
✅ Use consistent icon language
✅ Show ETA when available
✅ Use checkmark (✓) for completion

### Don'ts
❌ Don't use past tense during operation
❌ Don't show decimals in counts (3/10 not 3.5/10)
❌ Don't make status too long (>80 chars)
❌ Don't use technical jargon

---

## Testing Checklist

For each new progress indicator:

- [ ] Progress bar starts at 0 and ends at 1.0
- [ ] Status text is clear and informative
- [ ] ETA calculation works correctly (if applicable)
- [ ] Success message includes relevant statistics
- [ ] Toast notification appears on completion
- [ ] Error handling updates status appropriately
- [ ] Progress doesn't flicker with rapid updates
- [ ] All phases have meaningful progress values
- [ ] Icons are consistent with rest of app
- [ ] Works on both success and error paths

---

## Common Pitfalls

### 1. Progress Going Backward
```python
# ❌ Bad
progress_bar.progress(0.5)
# ... operation fails ...
progress_bar.progress(0.0)  # Don't reset!

# ✅ Good
progress_bar.progress(0.5)
# ... operation fails ...
# Leave progress where it is
```

### 2. Too Many Updates
```python
# ❌ Bad - Updates 1000 times
for i in range(1000):
    progress_bar.progress(i / 1000)  # Causes flicker

# ✅ Good - Updates every 10th item
for i in range(1000):
    if i % 10 == 0:
        progress_bar.progress(i / 1000)
```

### 3. Incorrect ETA Calculation
```python
# ❌ Bad - Division by zero
elapsed = time_elapsed()
eta = remaining / elapsed  # Crashes if elapsed = 0

# ✅ Good - Check first iteration
if i > 0:
    elapsed = time_elapsed()
    eta = (remaining / i) * elapsed
```

### 4. Forgetting Completion Updates
```python
# ❌ Bad - No final update
for item in items:
    process(item)
    progress_bar.progress(...)
# Missing final status!

# ✅ Good - Always complete
for item in items:
    process(item)
    progress_bar.progress(...)
status_text.text("✓ Complete!")
st.success("✅ Done")
```

---

## Performance Tips

1. **Batch updates** for large loops (every 10 items)
2. **Use spinners** for operations <5 seconds
3. **Avoid** complex string operations in tight loops
4. **Cache** datetime.datetime.now() calculations
5. **Test** with realistic data volumes
6. **Profile** if progress tracking adds >5% overhead

---

## Accessibility

- Status text is readable by screen readers
- Progress bars have semantic meaning
- Color is not the only indicator (icons + text)
- Success/error states are clearly distinguished
- Toast notifications don't auto-dismiss critical info

---

## Quick Reference Card

| Operation | Duration | Pattern | Example |
|-----------|----------|---------|---------|
| Multi-step workflow | >10s | Multi-Phase Progress | Onboarding wizard |
| Loop with LLM | >30s | Loop + ETA | Lead classification |
| Simple operation | <5s | Spinner | SERP tracking |
| Conditional feature | Variable | Conditional Progress | SEO audit |
| Large iteration | >50 items | Batched Updates | Page extraction |
| Nested operations | Variable | Nested Progress | Places details |

---

## Code Snippet Library

### Copy-Paste Templates

#### Basic Progress Bar
```python
progress_bar = st.progress(0.0)
status_text = st.empty()

status_text.text("Processing...")
progress_bar.progress(0.5)
# ... work ...
progress_bar.progress(1.0)
status_text.text("✓ Complete!")
```

#### Loop with Progress
```python
progress_bar = st.progress(0.0)
status_text = st.empty()
total = len(items)

for i, item in enumerate(items, 1):
    status_text.text(f"Processing {i}/{total}...")
    progress_bar.progress(i / total)
    process(item)

status_text.text("✓ Complete!")
st.success(f"✅ Processed {total} items")
```

#### With ETA
```python
start = datetime.datetime.now()
for i, item in enumerate(items):
    if i > 0:
        elapsed = (datetime.datetime.now() - start).total_seconds()
        eta = int((elapsed / i) * (total - i))
        eta_text = f" (ETA: {eta}s)"
    else:
        eta_text = ""
    status_text.text(f"Processing {i+1}/{total}{eta_text}")
    progress_bar.progress((i + 1) / total)
```

---

This reference guide provides all the patterns and best practices needed to implement consistent, user-friendly progress indicators throughout the application.
