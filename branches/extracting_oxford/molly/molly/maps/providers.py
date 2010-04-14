
class BaseMapsProvider(object):
    def import_data(self):
        pass
        
    def real_time_information(self, entity):
        return None
    
    def augment_metadata(self, entities):
        pass