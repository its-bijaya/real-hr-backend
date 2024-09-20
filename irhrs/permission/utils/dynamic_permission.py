"""@irhrs_docs"""
class DynamicHRSPermission:
    """Permission Class for permissions which are not stored in database"""

    def __init__(self, name, code):
        self.name = name
        self.code = code

    def __eq__(self, other):
        return self.code == other.code

    def __ne__(self, other):
        return self.code != other.code

    def __hash__(self):
        return hash((self.name, self.code))
