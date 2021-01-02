from tortoise.models import Model
from tortoise import fields


class Guild(Model):
    id = fields.TextField(pk=True)
    name = fields.TextField()
    prefix = fields.TextField(default='.')
    points = fields.IntField(null=True)
    role = fields.TextField(null=True)
    decay = fields.IntField(default=1)

    def __str__(self):
        return self.name


class Channel(Model):
    id = fields.TextField(pk=True)
    name = fields.TextField()
    guild = fields.ForeignKeyField('models.Guild', related_name='guild')

    def __str__(self):
        return self.name


class User(Model):
    id = fields.TextField(pk=True)
    name = fields.TextField()

    def __str__(self):
        return self.name


class Points(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User')
    guild = fields.ForeignKeyField('models.Guild')
    amount = fields.IntField(default=0)
    last_updated = fields.DatetimeField(auto_now=True)

    def __str__(self):
        return str(self.amount)


class Message(Model):
    id = fields.TextField(pk=True)
    content = fields.TextField()
    channel = fields.ForeignKeyField('models.Channel', related_name='channel')
    created_at = fields.DatetimeField()
    author = fields.ForeignKeyField('models.User', related_name='author')

    def __str__(self):
        return self.content
