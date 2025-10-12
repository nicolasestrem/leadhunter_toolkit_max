# Vertical Presets

This directory contains industry-specific configuration presets (verticals) that override scoring weights and keywords for specialized lead hunting.

## How Verticals Work

Vertical presets allow you to customize:
- **Scoring weights**: Adjust how emails, phones, social links, etc. are scored
- **Keywords**: Define industry-specific classification keywords
- **Priorities**: Focus on what matters most for that vertical

## Creating a Vertical Preset

Create a YAML file in this directory (e.g., `restaurants.yml`):

```yaml
name: "Restaurants"
description: "Restaurant and food service businesses"

# Custom scoring weights for this vertical
scoring:
  email_weight: 3.0         # Emails very important for reservations
  phone_weight: 5.0         # Phone critical for restaurants
  social_weight: 2.0        # Social media important for visibility
  about_or_contact_weight: 1.5
  city_match_weight: 2.0

# Industry-specific keywords for classification
keywords:
  restaurant:
    - restaurant
    - bistrot
    - bistro
    - café
    - brasserie
    - pizzeria
  cuisine:
    - cuisine
    - chef
    - menu
    - gastronomie
  service:
    - delivery
    - takeout
    - catering
    - livraison
```

## Example Verticals

### plumbing.yml
```yaml
name: "Plumbing"
description: "Plumbing and heating services"

scoring:
  phone_weight: 5.0         # Emergency contact critical
  email_weight: 2.0
  city_match_weight: 3.0    # Local service area important

keywords:
  plumbing:
    - plombier
    - plomberie
    - plumbing
  heating:
    - chauffage
    - heating
    - chaudière
```

### seo.yml
```yaml
name: "SEO & Digital Marketing"
description: "SEO and digital marketing agencies"

scoring:
  email_weight: 3.0
  phone_weight: 1.0
  social_weight: 4.0        # Strong social presence expected
  website_weight: 3.0

keywords:
  seo:
    - seo
    - référencement
    - search engine
  digital:
    - digital marketing
    - web marketing
    - content marketing
```

## Using Verticals

1. Create your vertical YAML file in this directory
2. In settings.json, set:
   ```json
   {
     "active_vertical": "restaurants"
   }
   ```
3. Vertical scoring and keywords will override defaults
4. Set to `null` or remove to disable vertical presets

## Notes

- Vertical presets are cached for performance
- Changes require restarting the app or clearing cache
- Missing verticals fall back to defaults silently
- Vertical weights override defaults, not merge with them
