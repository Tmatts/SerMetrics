# Scrath file for Salesforce API interactions

def query(self, query):
        return self.sf.query_all(query)
def query_all(self, query):
    return self.sf.query_all(query)
def query_one(self, query):
    return self.sf.query(query)
def get_record(self, object_name, record_id):
    return self.sf.get(object_name, record_id)
def create_record(self, object_name, data):
    return self.sf.create(object_name, data)
def update_record(self, object_name, record_id, data):
    return self.sf.update(object_name, record_id, data)
def delete_record(self, object_name, record_id):
    return self.sf.delete(object_name, record_id)
def describe_object(self, object_name):
    return self.sf.__getattr__(object_name).describe()
def describe_global(self):
    return self.sf.describe()
def get_user_info(self):
    return self.sf.get_user_info()
def get_limits(self):
    return self.sf.limits()
def get_recent(self):
    return self.sf.recent()
def get_versions(self):
    return self.sf.versions()
def get_resources(self):
    return self.sf.resources()
def get_sobjects(self):
    return self.sf.get_sobjects()
def get_metadata(self, object_name):
    return self.sf.__getattr__(object_name).metadata()
def get_layout(self, object_name, layout_type):
    return self.sf.__getattr__(object_name).layout(layout_type)
def get_approval_layout(self, object_name):
    return self.sf.__getattr__(object_name).approval_layout()
def get_describe_layouts(self, object_name):
    return self.sf.__getattr__(object_name).describe_layouts()
def get_describe_layout(self, object_name, record_type_id):
    return self.sf.__getattr__(object_name).describe_layout(record_type_id)
def get_describe_layouts_by_record_type(self, object_name, record_type_id):
    return self.sf.__getattr__(object_name).describe_layouts_by_record_type(record_type_id)
def get_describe_tabs(self, object_name):
    return self.sf.__getattr__(object_name).describe_tabs()
def get_describe_search_scope_order(self, object_name):
    return self.sf.__getattr__(object_name).describe_search_scope_order()