from typing import Optional


class ServiceNotesManager:
    @staticmethod
    def add_note(existing_notes: Optional[str], new_note: str) -> str:
        if not new_note.strip():
            return existing_notes or ""
        
        if not existing_notes:
            return new_note.strip()
        
        existing_normalized = ServiceNotesManager._normalize_notes(existing_notes)
        new_normalized = ServiceNotesManager._normalize_note(new_note)
        
        if new_normalized in existing_normalized:
            return existing_notes
        
        return f"{existing_notes} | {new_note.strip()}"
    
    @staticmethod
    def _normalize_notes(notes: str) -> set:
        if not notes:
            return set()
        
        import re
        parts = re.split(r'[|\r\n]+', notes)
        normalized = set()
        
        for part in parts:
            part = part.strip()
            if part:
                normalized.add(ServiceNotesManager._normalize_note(part))
        
        return normalized
    
    @staticmethod
    def _normalize_note(note: str) -> str:
        normalized = note.lower().strip()
        
        if 'extensión sin pago' in normalized:
            return 'extension_without_payment'
        elif 'pago simultáneo' in normalized:
            return 'simultaneous_payment'
        elif 'renovación' in normalized and 'pago' in normalized:
            return 'renewal_with_payment'
        
        return normalized
    
    @staticmethod
    def clean_notes(notes: Optional[str]) -> str:
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
            
            normalized = ServiceNotesManager._normalize_note(part)
            
            if normalized not in seen:
                cleaned_parts.append(part)
                seen.add(normalized)
        
        return '\n'.join(cleaned_parts)
