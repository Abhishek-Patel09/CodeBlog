from django.db import models
from django.contrib.auth.models import User
from .utils import Preference as Pref
from pygments import lexers, highlight
from pygments.formatters import HtmlFormatter, ClassNotFound
from django.shortcuts import reverse
import time
from django.utils.text import slugify
from django.dispatch import receiver
from django.db.models.signals import post_save

# Create your models here.
class Language(models.Model):
    name = models.CharField(max_length=100)
    lang_code = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    mime = models.CharField(max_length=100, help_text='MIME to use when sending snippet as a file.')
    file_extension = models.CharField(max_length=10)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def get_lexer(self):
        return lexers.get_lexer_by_name(self.lang_code)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('codeblog:trending_snippets', args=[self.slug])

def get_default_language():
    lang = Language.objects.get_or_create(
        name = 'Plain Text',
        lang_code = 'text',
        slug = 'text',
        mime = 'text/plain',
        file_extension = '.txt',
    )

    return lang[0].id

class Author(models.Model):
    user = models.OneToOneField(User, related_name = 'profile', on_delete=models.CASCADE)
    default_language = models.ForeignKey(Language, on_delete=models.CASCADE, default = get_default_language)
    default_exposure = models.CharField(max_length=10, choices=Pref.exposure_choices, default = Pref.SNIPPET_EXPOSURE_PUBLIC)
    private = models.BooleanField(default=False)
    views = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username

    def get_absolute_url(self):
        return reverse('codeblog:profile',args=[self.user.username])

    def get_snippet_count(self):
        return self.user.snippet_set.count()

    def get_preferences(self):
        return {'language': self.default_language.id, 'exposure': self.default_exposure}

    def get_absolute_url(self):
        return reverse('codeblog:profile', args=[self.user.username])

@receiver(post_save, sender=User)
def create_author(sender, **kwargs):
    if kwargs.get('created', False):
        Author.objects.get_or_create(user=kwargs.get('instance'))

class Snippet(models.Model):
    title = models.CharField(max_length=200, blank=True)
    original_code = models.TextField()
    highlighted_code = models.TextField()
    #expiration = models.CharField(max_length=10, choices=Pref.expiration_choices)
    exposure = models.CharField(max_length=10, choices=Pref.exposure_choices)
    hits = models.IntegerField(default=0)
    slug = models.SlugField()
    created_on = models.DateTimeField(auto_now_add=True)

    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tags = models.ManyToManyField('Tag', blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = str(time.time()).replace(".", "")
        self.highlighted_code = self.highlight()
        if not self.title:
            self.title = "Untitled"
        super(Snippet, self).save(*args, **kwargs)

    class Meta:
        ordering = ['-created_on']

    def highlight(self):
        formatter = HtmlFormatter(linenos=True)
        return highlight(self.original_code, self.language.get_lexer(), formatter)

    def __str__(self):
        return self.language.name

    def get_absolute_url(self):
        return reverse('codeblog:snippet_detail', args=[self.slug])

class Tag(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.CharField(max_length=200, unique=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Tag, self).save(*args, **kwargs)

    class Meta:
        ordering  = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('codeblog:tag_list', args=[self.slug])
