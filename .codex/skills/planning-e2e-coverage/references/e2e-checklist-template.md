# E2E Checklist Template

Use this file as a promptable structure, not a rigid copy-paste template. Keep the final checklist aligned to the current product and omit sections that do not apply.

## Core Sections

### 1. Purpose

State what the checklist is protecting:

- key user journeys
- important browser interactions
- responsive behavior
- visual stability

### 2. Required Viewports

Choose sizes from product context.

Suggested defaults for web products:

- small mobile
- medium tablet or narrow laptop
- large desktop

If the app is desktop-first or mobile-only, say so explicitly and adjust coverage.

### 3. Global Checks

Apply these to each critical screen:

- page loads without fatal errors
- primary heading is visible
- primary CTA is visible and clickable
- no horizontal overflow
- important text is readable
- cards and panels stay inside viewport bounds
- scrolling works when content is taller than the viewport

### 4. User Journey Checks

List the highest-value flows first. For each flow, verify:

- entry point
- input actions
- primary CTA click
- state transition
- success state
- failure state where relevant

Examples of flow naming:

- auth flow
- checkout flow
- record-and-submit flow
- search-and-filter flow
- create-edit-delete flow
- archive-to-detail flow

### 5. Screen-by-Screen Interaction Checks

For each critical screen, break down:

- primary CTA
- important secondary CTAs
- toggles, filters, tabs, modals, drawers
- form inputs
- validation feedback

Do not stop at "button exists." Verify what changes after clicking.

### 6. State Coverage

Consider these states when relevant:

- success
- error
- loading
- empty
- populated
- unauthorized
- not-found
- retry

If a state does not apply, leave it out rather than padding the checklist.

### 7. Responsive and Layout Checks

Look for:

- horizontal overflow
- clipped text
- overlapping cards
- off-screen CTAs
- awkward line wrapping
- broken sticky headers or nav
- unusable modal or drawer sizing

Recommended assertion pattern:

```ts
const hasOverflow = await page.evaluate(() => document.body.scrollWidth > window.innerWidth);
expect(hasOverflow).toBe(false);
```

### 8. Visual Regression Review

Recommend screenshots for the highest-value states:

- landing or home
- primary input screen
- success result screen
- error state
- list or archive screen
- detail screen

Manual review should look for:

- clipping
- overlap
- hidden actions
- unstable spacing
- decorative effects obscuring content

### 9. Suggested Test Buckets

Propose `tests/e2e` buckets that match product behavior, not arbitrary naming. Common patterns:

- `smoke-*.spec.ts`
- `primary-flow.spec.ts`
- `error-states.spec.ts`
- `responsive-layout.spec.ts`
- `auth-flow.spec.ts`
- `dashboard-flow.spec.ts`
- `checkout-flow.spec.ts`
- `editor-flow.spec.ts`

Split by user journey or risk area, not by tiny component details.

### 10. Release Gate

Define the minimum bar before calling the feature ready:

- unit tests pass
- integration tests pass
- E2E suite passes
- responsive checks pass
- screenshots reviewed when UI risk is meaningful
- no critical blocked CTA or overflow issue remains

## Plan-Strengthening Prompts

If an existing implementation plan is light on E2E coverage, add or expand tasks that include:

- button-level interaction coverage
- state-based scenario coverage
- responsive assertions
- screenshot/manual review steps
- stable selector or test-id guidance where needed

## Anti-Patterns

Avoid these weak outputs:

- route loads, therefore coverage is done
- one giant E2E file for every flow
- only happy-path coverage
- no responsive checks
- no manual visual review recommendation for UI-heavy products
- generic checklist language that ignores the actual product
