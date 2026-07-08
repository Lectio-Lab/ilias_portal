from django.db import models

from apps.accounts.models import User


class CourseCache(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="course_caches"
    )
    course_id = models.IntegerField()
    title = models.CharField(max_length=500)
    url = models.URLField(max_length=1000)
    role = models.CharField(max_length=100, blank=True)
    last_refreshed = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ilias_coursecache"
        unique_together = ["user", "course_id"]
        ordering = ["title"]
        verbose_name = "course cache"
        verbose_name_plural = "course caches"

    def __str__(self):
        return f"{self.title} ({self.course_id}) — {self.user.email}"
