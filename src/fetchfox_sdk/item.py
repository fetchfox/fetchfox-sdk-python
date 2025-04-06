class Item:
    """
    Wrapper for result items that provides attribute access with dot notation
    while maintaining dictionary-like compatibility.
    """
    def __init__(self, data):
        self._data = data

    def __getattr__(self, name):
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'Item' object has no attribute '{name}'")

    def __getitem__(self, key):
        return self._data[key]

    def __contains__(self, item):
        return item in self._data

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return f"Item({self._data})"

    def __str__(self):
        return str(self._data)

    # Support dict() conversion
    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    def values(self):
        return self._data.values()

    def to_dict(self):
        """Convert back to a regular dictionary."""
        return self._data.copy()

    def get(self, key, default=None):
        """Get a value with a default if the key doesn't exist."""
        return self._data.get(key, default)

    def __eq__(self, other):
        if isinstance(other, Item):
            return self._data == other._data
        elif isinstance(other, dict):
            return self._data == other
        return False

    def __bool__(self):
        return bool(self._data)