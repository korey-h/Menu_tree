from django.core.exceptions import ValidationError
from django.db import models


class Tags(models.Model):
    name = models.CharField(
        verbose_name='название пункта',
        max_length=25)
    slug = models.SlugField(max_length=25, unique=True)
    parent = models.ForeignKey(
        'Tags',
        on_delete=models.SET_NULL,
        verbose_name='Вышестоящий пункт',
        related_name='childs',
        null=True,
        blank=True)
    url = models.CharField(
        verbose_name='ссылка',
        max_length=500,
        blank=True,
        unique=True)

    autourl = models.BooleanField(
        verbose_name='Автозаполнение URL',
        default=True,
    )

    def __str__(self) -> str:
        return self.name

    def as_html(self, lvl: int = 0, bold: bool = False, url: str = ''):
        offset = "-" * lvl * 4 + '> '
        name = self.name
        url = self.url if url == '' else url
        if bold:
            name = f'<b>{name}</b>'
        return f'<p>{offset}<a href="{url}">{name}</a></p>\n'

    def clean(self):

        def loop_check(testing: Tags = self, parent: Tags = self.parent):
            if not parent:
                return
            childs = testing.childs.all()
            if not childs.exists():
                return
            if parent in childs:
                raise ValidationError(
                    f'Нельзя назначить пункт {parent} вышестоящим,'
                    f'т.к. сейчас он является дочерним для {testing}'
                )
            for child in childs:
                loop_check(child, parent)

        if self.parent == self:
            raise ValidationError(
                f'Нельзя назначить пункт {self.parent} вышестоящим,'
                'т.к. является текущим'
            )

        loop_check()
        super().clean()

    def save(self, *args, **kwargs):

        def relation_url_renew(tag: Tags):
            childs = tag.childs.all()
            if not childs.exists():
                return
            for child in childs:
                if child.autourl:
                    child.url = f'{tag.url}/{child.slug}'
                    relation_url_renew(child)
                    child.save()

        if self.autourl:
            if self.parent:
                self.url = f'{self.parent.url}/{self.slug}'
            else:
                self.url = f'/{self.slug}'
            relation_url_renew(self)
        super(Tags, self).save(*args, **kwargs)
