from django.db.models import Exists, OuterRef

class BusinessLineService:
    
    @staticmethod
    def check_line_has_active_services(business_line):
        return business_line.client_services.filter(is_active=True).exists()
    
    @staticmethod
    def check_line_has_active_sublines(business_line):
        for child in business_line.children.all():
            if BusinessLineService.check_line_has_active_services(child):
                return True
            if BusinessLineService.check_line_has_active_sublines(child):
                return True
        return False
    
    @staticmethod
    def update_business_line_status(business_line):
        has_active_services = BusinessLineService.check_line_has_active_services(business_line)
        has_active_sublines = False
        
        if not has_active_services:
            has_active_sublines = BusinessLineService.check_line_has_active_sublines(business_line)
        
        new_status = has_active_services or has_active_sublines
        if business_line.is_active != new_status:
            business_line.is_active = new_status
            business_line.save(update_fields=['is_active'])
            if business_line.parent:
                BusinessLineService.update_business_line_status(business_line.parent)
    
    @staticmethod
    def update_all_business_lines_status():
        from apps.business_lines.models import BusinessLine
        
        leaf_lines = BusinessLine.objects.filter(
            ~Exists(BusinessLine.objects.filter(parent=OuterRef('pk')))
        )
        
        for line in leaf_lines:
            BusinessLineService.update_business_line_status(line)
