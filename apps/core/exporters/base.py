class BaseExporter:
  
    def __init__(self):
        self.name = self.__class__.__name__
    
    def get_data(self):
        raise NotImplementedError("Subclasses must implement get_data()")
    
    def get_name(self):
        return self.name.replace('Exporter', '').lower()
