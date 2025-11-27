# Yalla Restaurant Discovery Platform - Design Guidelines

## Design Approach
**Reference-Based: Food Discovery Platforms**
Drawing inspiration from Zomato, Yelp, and modern food discovery apps, adapted for Saudi market with bilingual support (Arabic/English) and cultural sensitivity. Focus on visual storytelling through food photography and community trust-building.

## Typography System
- **Primary Font**: Inter or Cairo (for better Arabic support) via Google Fonts
- **Hierarchy**:
  - Hero Headlines: 48-64px, bold weight
  - Section Titles: 32-40px, semibold
  - Restaurant Names: 24px, semibold
  - Body Text: 16px, regular
  - Captions/Meta: 14px, medium
- **RTL Support**: Implement full bidirectional text support for Arabic/English switching

## Layout & Spacing System
**Tailwind Spacing Units**: Consistently use 2, 4, 8, 12, 16 units throughout
- Section padding: py-16 to py-24
- Card spacing: p-6 to p-8
- Element gaps: gap-4 to gap-8
- Container max-width: max-w-7xl for main content

## Core Page Structures

### Homepage
1. **Hero Section** (80vh): Full-width food photography hero with search bar overlay, headline "Discover Jeddah's Hidden Culinary Gems" in both Arabic/English, blurred-background CTA buttons
2. **Promoted Restaurants Grid**: 3-column grid (lg:grid-cols-3 md:grid-cols-2) with restaurant cards showing image, name, cuisine type, rating stars, review count
3. **Cuisine Categories**: Horizontal scrollable cards with cuisine type icons and names (Saudi, Italian, Mexican, Asian, etc.)
4. **Top Reviewers**: 4-column grid showcasing community leaders with avatar, name, review count, badge
5. **How It Works**: 3-column feature explanation with icons (Discover → Review → Share)
6. **CTA Section**: Community call-to-action with supporting text about supporting local businesses

### Restaurant Listing Page
- **Filter Sidebar** (sticky, left side, 300px width): Cuisine type checkboxes, price range, rating filter, location tags
- **Results Grid** (2-column lg:grid-cols-2): Restaurant cards with 16:9 aspect ratio image, name, cuisine badges, star rating, brief description, distance indicator
- **Map Toggle**: Switch between grid and map view

### Restaurant Detail Page
- **Image Gallery**: Large hero image (600px height) with thumbnail carousel
- **Info Panel**: Restaurant name (40px), cuisine badges, rating summary with star distribution bars, working hours, location with map embed, price range indicator
- **Menu Section**: Categorized dishes with images in 3-column grid
- **Reviews Section**: Individual review cards with user avatar, name, date, star rating, review text, helpful vote buttons

### User Profile/Dashboard
- **Profile Header**: User avatar (large, 120px), name, join date, total reviews badge
- **Stats Cards**: 4-column grid showing reviews written, photos uploaded, helpful votes, restaurants visited
- **Activity Feed**: Timeline of recent reviews with restaurant thumbnails

## Component Library

### Navigation
- **Desktop**: Horizontal nav with logo left, search bar center, user menu/login right
- **Mobile**: Hamburger menu with slide-out drawer

### Restaurant Cards
- 16:9 aspect ratio image with rounded corners (rounded-xl)
- Hover: subtle scale transform (scale-105)
- Badge overlays for "New", "Trending", "Small Business"
- Star rating component (filled/unfilled stars)

### Review Cards
- User avatar (48px circular)
- 5-star rating display
- Date and helpful count
- Expandable text (show more/less)
- Image attachment thumbnails in horizontal scroll

### Forms
- Floating labels for inputs
- Multi-step restaurant submission wizard
- Star rating selector (interactive)
- Tag selector with chips
- Image upload with preview

### Search & Filters
- Prominent search bar with autocomplete dropdown
- Filter chips that are removable
- Active filter count badge
- Clear all filters option

## Images Strategy
**Critical**: Use high-quality food and restaurant photography throughout:
- **Hero**: Vibrant Jeddah restaurant scene or iconic Saudi dish
- **Restaurant Cards**: Exterior or signature dish photos
- **Detail Pages**: Multiple angles (exterior, interior, dishes, ambiance)
- **Category Icons**: Food-specific illustrations
- **Empty States**: Friendly illustrations for no results/reviews
- **User Avatars**: Circular placeholders until user uploads

## Interaction Patterns
- Infinite scroll on restaurant listings
- Modal overlays for image galleries
- Toast notifications for actions (review submitted, restaurant added)
- Skeleton loading states for content
- Sticky header on scroll
- Back-to-top button appears after scrolling

## Accessibility & RTL
- Full keyboard navigation support
- ARIA labels on all interactive elements
- Text directionality switches seamlessly (dir="rtl" / dir="ltr")
- Mirrored layouts for RTL (flip navigation, alignment)
- High contrast ratios for readability

## Icon Library
**Heroicons** (via CDN) for all interface icons: star (ratings), map-pin (location), clock (hours), users (reviews), search, filter, heart (favorites), camera (photos)

This design creates a visually rich, community-driven platform that celebrates Jeddah's food culture while maintaining professional credibility and ease of use.