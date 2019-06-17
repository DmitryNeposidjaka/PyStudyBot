class Task:
    category = ''
    content = ''
    comment = ''
    user_id = ''
    approved = False
    approved_by = ''
    deleted = False

    def __init__(self):
        self.approved = False
        self.approved_by = ''
        self.deleted = False

    def to_dict(self):
        return self.__dict__
