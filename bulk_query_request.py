from dataclasses import dataclass
from base_salesforce_request import BaseSalesforceRequest

@dataclass
class BulkQueryRequest(BaseSalesforceRequest):
    query: str
    operation: str = "query"
    contentType: str = "JSON"
    lineEnding: str = "LF"

    def to_dict(self):
        return {
            "operation": self.operation,
            "query": self.query,
            "contentType": self.contentType,
            "lineEnding": self.lineEnding
        }
