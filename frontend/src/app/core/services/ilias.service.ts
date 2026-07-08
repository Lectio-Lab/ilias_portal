import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Course, CourseContents } from '../models/course.model';

export interface RefreshResult {
  message: string;
  courses_found?: number;
}

export interface PublishResult {
  url?: string;
  message?: string;
  success?: boolean;
}

@Injectable({ providedIn: 'root' })
export class IliasService {
  private readonly baseUrl = 'http://localhost:8000/api/ilias';

  constructor(private http: HttpClient) {}

  getCourses(): Observable<Course[]> {
    return this.http.get<Course[]>(`${this.baseUrl}/courses/`);
  }

  refreshCourses(): Observable<RefreshResult> {
    return this.http.post<RefreshResult>(`${this.baseUrl}/courses/refresh/`, {});
  }

  getCourseContents(courseId: number): Observable<CourseContents> {
    return this.http.get<CourseContents>(
      `${this.baseUrl}/courses/${courseId}/contents/`
    );
  }

  publishAssignment(
    courseId: number,
    data: {
      title: string;
      instruction: string;
      deadline_date?: string;
      deadline_time?: string;
    },
    file?: File
  ): Observable<PublishResult> {
    const formData = new FormData();
    formData.append('title', data.title);
    formData.append('instruction', data.instruction);
    
    if (data.deadline_date) {
      const parts = data.deadline_date.split('-');
      if (parts.length === 3) {
        const yyyy = parts[0];
        const mm = parts[1];
        const dd = parts[2];
        const timeStr = data.deadline_time ? data.deadline_time : '23:59';
        formData.append('deadline', `${dd}.${mm}.${yyyy} ${timeStr}`);
      }
    }
    
    if (file) formData.append('file', file, file.name);

    return this.http.post<PublishResult>(
      `${this.baseUrl}/courses/${courseId}/publish/assignment/`,
      formData
    );
  }

  publishSlides(
    courseId: number,
    data: { folder_title: string; description?: string },
    files: File[]
  ): Observable<PublishResult> {
    const formData = new FormData();
    formData.append('folder_title', data.folder_title);
    if (data.description) formData.append('description', data.description);
    files.forEach((f) => formData.append('files', f, f.name));

    return this.http.post<PublishResult>(
      `${this.baseUrl}/courses/${courseId}/publish/slides/`,
      formData
    );
  }

  publishAnnouncement(
    courseId: number,
    data: {
      title: string;
      content: string;
      visibility: 'users' | 'public';
    }
  ): Observable<PublishResult> {
    return this.http.post<PublishResult>(
      `${this.baseUrl}/courses/${courseId}/publish/announcement/`,
      data
    );
  }

  getDownloadUrl(url: string): string {
    const encoded = encodeURIComponent(url);
    return `${this.baseUrl}/download/?url=${encoded}`;
  }
}
