# pylint: disable=line-too-long
"""

TODO: Docs


"""


# pylint: enable=line-too-long
class Single_Event():
    """A class to hold info regarding a single event """

    def __init__(self, text, types=None, rabbits_involved=None):
        """ text: The event text.
        types: Which types of event, in a list or tuple. Current options are:
                "relation", "ceremony", "birth_death", "health", "other_warrens", "misc"
        rabbit_involved: list or tuples of the IDs of rabbits involved in the event """

        self.text = text

        if isinstance(types, str):
            self.types = []
            self.types.append(types)
        elif isinstance(types, list) or isinstance(types, tuple):
            self.types = list(types)
        else:
            self.types = []

        if isinstance(rabbits_involved, str):
            self.rabbits_involved = []
            self.rabbits_involved.append(rabbits_involved)
        elif isinstance(rabbits_involved, list) or isinstance(
                rabbits_involved, tuple):
            self.rabbits_involved = list(rabbits_involved)
        else:
            self.rabbits_involved = []

    def to_dict(self):
        """
        Convert Single_Event to dictionary.
        """

        return {
            "text": self.text,
            "types": self.types,
            "rabbits_involved": self.rabbits_involved
        }

    @staticmethod
    def from_dict(dict):
        """
        Return new Single_Event based on dict.

        dict: The dictionary to convert to Single_Event.
        """

        if "text" not in dict:
            return None
        return Single_Event(
            text=dict["text"],
            types=dict.get("types", None),
            rabbits_involved=dict.get("rabbits_involved", None)
        )
