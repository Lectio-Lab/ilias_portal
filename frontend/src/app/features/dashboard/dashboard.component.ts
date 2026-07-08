import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { IliasService } from '../../core/services/ilias.service';
import { User, IliasCredential } from '../../core/models/user.model';
import { Course } from '../../core/models/course.model';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
})
export class DashboardComponent implements OnInit {
  user: User | null = null;
  courses: Course[] = [];
  credentials: IliasCredential | null = null;
  loadingUser = true;
  loadingCourses = true;
  hasCredentials = false;

  constructor(
    private authService: AuthService,
    private iliasService: IliasService
  ) {}

  ngOnInit(): void {
    this.authService.getProfile().subscribe({
      next: (u) => {
        this.user = u;
        this.loadingUser = false;
      },
      error: () => (this.loadingUser = false),
    });

    this.authService.getIliasCredentials().subscribe({
      next: (creds) => {
        this.credentials = creds;
        this.hasCredentials = !!creds?.ilias_username;
      },
      error: () => (this.hasCredentials = false),
    });

    this.iliasService.getCourses().subscribe({
      next: (c) => {
        this.courses = c;
        this.loadingCourses = false;
      },
      error: () => (this.loadingCourses = false),
    });
  }

  get greeting(): string {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  }

  get displayName(): string {
    if (!this.user) return '';
    return this.user.first_name || this.user.email;
  }
}
