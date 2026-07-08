import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { IliasService } from '../../core/services/ilias.service';

export type PublishMode = 'assignment' | 'slides' | 'announcement';

@Component({
  selector: 'app-publish',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './publish.component.html',
  styleUrls: ['./publish.component.scss'],
})
export class PublishComponent implements OnInit {
  publishMode: PublishMode = 'assignment';
  form!: FormGroup;
  loading = false;
  successMessage = '';
  publishUrl = '';
  errorMessage = '';

  // File state
  selectedFile: File | null = null;
  selectedFiles: File[] = [];

  constructor(
    private fb: FormBuilder,
    private iliasService: IliasService
  ) {}

  ngOnInit(): void {
    this.buildForm();
  }

  setMode(mode: PublishMode): void {
    this.publishMode = mode;
    this.successMessage = '';
    this.publishUrl = '';
    this.errorMessage = '';
    this.selectedFile = null;
    this.selectedFiles = [];
    this.buildForm();
  }

  private buildForm(): void {
    const commonFields = {
      courseId: ['', [Validators.required, Validators.pattern(/^[0-9]+$/)]],
    };

    switch (this.publishMode) {
      case 'assignment':
        this.form = this.fb.group({
          ...commonFields,
          title: ['', [Validators.required, Validators.minLength(3)]],
          instruction: ['', [Validators.required, Validators.minLength(10)]],
          deadline_date: [''],
          deadline_time: [''],
        });
        break;

      case 'slides':
        this.form = this.fb.group({
          ...commonFields,
          folder_title: ['', [Validators.required, Validators.minLength(3)]],
          description: [''],
        });
        break;

      case 'announcement':
        this.form = this.fb.group({
          ...commonFields,
          title: ['', [Validators.required, Validators.minLength(3)]],
          content: ['', [Validators.required, Validators.minLength(10)]],
          visibility: ['users', Validators.required],
        });
        break;
    }
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files?.length) {
      this.selectedFile = input.files[0];
    }
  }

  onFilesSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files?.length) {
      this.selectedFiles = Array.from(input.files);
    }
  }

  removeFile(index: number): void {
    this.selectedFiles.splice(index, 1);
  }

  formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  onSubmit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    if (this.publishMode === 'slides' && this.selectedFiles.length === 0) {
      this.errorMessage = 'Please select at least one file to upload.';
      return;
    }

    this.loading = true;
    this.errorMessage = '';
    this.successMessage = '';
    this.publishUrl = '';

    const courseId = Number(this.form.value.courseId);

    const obs$ = (() => {
      switch (this.publishMode) {
        case 'assignment':
          return this.iliasService.publishAssignment(
            courseId,
            this.form.value,
            this.selectedFile ?? undefined
          );

        case 'slides':
          return this.iliasService.publishSlides(
            courseId,
            {
              folder_title: this.form.value.folder_title,
              description: this.form.value.description
            },
            this.selectedFiles
          );

        case 'announcement':
          return this.iliasService.publishAnnouncement(
            courseId,
            this.form.value
          );
      }
    })();

    obs$.subscribe({
      next: (result) => {
        this.loading = false;
        this.successMessage = 'Published successfully!';
        if (result.url) {
          this.publishUrl = result.url;
        }
      },
      error: (err) => {
        this.loading = false;
        if (err.status === 0) {
          this.errorMessage = 'Cannot connect to server.';
        } else {
          this.errorMessage = err.error?.detail || err.error?.message || 'Publish failed. Please try again.';
        }
      },
    });
  }
}
