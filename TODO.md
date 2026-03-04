# TODO - GIS Sidebar Typography Update

## Task
Update sidebar typography for better readability and accessibility

## Changes Required

- [x] Analyze current CSS typography in app.py
- [x] Implement Navigation & Headers: 14px, Semi-bold (600)
- [x] Implement Layer List & Inputs: 12px, Regular (400)
- [x] Implement Supplementary Info: 10-11px, Regular (400)
- [x] Verify contrast ratio meets 4.5:1 requirement
- [x] Test the application

## Implementation Details

### 1. Navigation & Headers (.section-title)
- Size: 14px
- Weight: 600 (Semi-bold)
- Applied to: Sidebar section titles

### 2. Layer List & Inputs
- Size: 12px
- Weight: 400 (Regular)
- Applied to: Input fields, select boxes, multi-selects, sliders

### 3. Supplementary Info
- Size: 10-11px
- Weight: 400 (Regular)
- Applied to: Metric labels, coordinates, metadata

### 4. Contrast
- Current text: #eaeaea on background #1a1a2e
- Current ratio: ~14:1 (meets 4.5:1 requirement)

## Sidebar CSS Fix (Completed)
- ✅ Removed conflicting `max-width` definitions (260px vs 20vw)
- ✅ Simplified to single consistent width: 280px
- ✅ Removed conflicting/circular CSS declarations

