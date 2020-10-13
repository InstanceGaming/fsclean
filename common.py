import json


class ChangeLog:
    """
    A keeper of changes to files
    """

    @property
    def changes(self):
        """
        :return: the list of changes
        """
        return self._changes
    
    @property
    def counter(self):
        """
        :return: the total number of recorded changes
        """
        return self._counter

    def __init__(self):
        self._counter = 0
        self._changes = []
        self._root = {
            'changes': self._changes
        }

    def addChange(self, operation: str, action: str, executed: bool, **kwargs):
        """
        Record a new operation
        :param operation: Arbitrary name of the operation
        :param action:  Arbitrary action name
        :param executed: Weather the action was carried out
        :param kwargs: Any related data that will be appended
        """
        change = {
            'id': self._counter,
            'operation': operation,
            'action': action,
            'executed': executed
        }
        change.update(kwargs)
        self._changes.append(change)
        self._counter += 1

    def addRootProperties(self, properties: dict):
        """
        Add data to the root object
        :param properties: a dictionary of additional data
        """
        self._root.update(properties)

    def save(self, path: str, **kwargs):
        """
        Write the changes to a file in JSON
        :param path: the path to write to
        :param kwargs: parameters to pass to the JSON encoder
        """
        with open(path, 'w') as sf:
            json.dump(self._root, sf, **kwargs)
