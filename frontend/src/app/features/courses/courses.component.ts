import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { IliasService } from '../../core/services/ilias.service';
import { Course } from '../../core/models/course.model';

@Component({
  selector: 'app-courses',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './courses.component.html',
  styleUrls: ['./courses.component.scss'],
})
export class CoursesComponent implements OnInit {
  courses: Course[] = [];
  loading = true;
  refreshing = false;
  refreshProgress = '';
  refreshError = '';
  refreshSuccess = '';
  errorMessage = '';

  private progressMessages = [
    'Connecting to ILIAS…',
    'Authenticating with university server…',
    'Fetching your enrolled courses…',
    'Processing course data…',
    'Almost done…',
  ];
  private progressIndex = 0;
  private progressInterval: ReturnType<typeof setInterval> | null = null;

  constructor(private iliasService: IliasService) {}

  ngOnInit(): void {
    this.loadCourses();
  }

  loadCourses(): void {
    this.loading = true;
    this.errorMessage = '';
    this.iliasService.getCourses().subscribe({
      next: (c) => {
        this.courses = c;
        this.loading = false;
      },
      error: (err) => {
        this.loading = false;
        if (err.status === 0) {
          this.errorMessage = 'Cannot connect to server.';
        } else {
          this.errorMessage = 'Failed to load courses.';
        }
      },
    });
  }

  refreshCourses(): void {
    if (this.refreshing) return;

    this.refreshing = true;
    this.refreshError = '';
    this.refreshSuccess = '';
    this.progressIndex = 0;
    this.refreshProgress = this.progressMessages[0];

    this.progressInterval = setInterval(() => {
      this.progressIndex =
        (this.progressIndex + 1) % this.progressMessages.length;
      this.refreshProgress = this.progressMessages[this.progressIndex];
    }, 4000);

    this.iliasService.refreshCourses().subscribe({
      next: (result) => {
        this.stopProgress();
        this.refreshSuccess = result.message || `Successfully refreshed! Found ${result.courses_found ?? this.courses.length} courses.`;
        this.loadCourses();
      },
      error: (err) => {
        this.stopProgress();
        if (err.status === 401) {
          this.refreshError = 'Authentication failed. Please check your ILIAS credentials.';
        } else if (err.status === 0) {
          this.refreshError = 'Cannot connect to server.';
        } else {
          this.refreshError = err.error?.detail || 'Refresh failed. Please try again.';
        }
      },
    });
  }

  private stopProgress(): void {
    this.refreshing = false;
    this.refreshProgress = '';
    if (this.progressInterval) {
      clearInterval(this.progressInterval);
      this.progressInterval = null;
    }
  }

  getRoleBadgeClass(role?: string): string {
    if (!role) return 'badge-muted';
    const r = role.toLowerCase();
    if (r.includes('admin') || r.includes('tutor') || r.includes('instructor')) {
      return 'badge-warning';
    }
    return 'badge-primary';
  }

  trackByCourseId(_: number, course: Course): number {
    return course.course_id;
  }
}
