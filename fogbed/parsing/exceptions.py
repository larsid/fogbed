
class ParseLinksException(Exception):
    pass

class ParseContainersException(Exception):
    pass

class ParseTunnelsException(Exception):
    pass

class ParseVirtualInstances(Exception):
    pass

class ParseWorkersException(Exception):
    pass

class SectionNotFound(Exception):
    def __init__(self, section: str) -> None:
        super().__init__(f"Section '{section}' was not found")