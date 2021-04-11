

class Debuger:
    def __init__(self, verbosity=1):
        self.verbosity=verbosity

    def v_print(self, level, *msg) -> None:
        """
        prints message if VERBOSITY is high enough

        Args:
            level: minimum level for message to print
            msg: message list

            Returns:
            None
    """
        if(self.verbosity >= level):
            print(*msg)
