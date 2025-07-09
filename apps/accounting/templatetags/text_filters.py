from django import template

register = template.Library()


@register.filter
def clean_duplicate_notes(notes):
    if not notes:
        return ""
    
    import re
    parts = re.split(r'[|\r\n]+', notes)
    seen = set()
    cleaned_parts = []
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        normalized = part.lower().strip()
        
        if 'extensión sin pago' in normalized:
            if 'extension_noted' not in seen:
                cleaned_parts.append("Extensión sin pago realizada")
                seen.add('extension_noted')
        elif normalized not in seen:
            cleaned_parts.append(part)
            seen.add(normalized)
    
    return '\n'.join(cleaned_parts)


@register.filter
def format_service_notes(notes):
    if not notes:
        return ""
    
    cleaned = clean_duplicate_notes(notes)
    
    parts = cleaned.split('\n')
    parts = [part.strip() for part in parts if part.strip()]
    
    if len(parts) > 1:
        formatted = []
        for i, part in enumerate(parts, 1):
            formatted.append(f"{i}. {part}")
        return '\n'.join(formatted)
    
    return cleaned
