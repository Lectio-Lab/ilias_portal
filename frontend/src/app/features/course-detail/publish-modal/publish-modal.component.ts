import {
  Component,
  EventEmitter,
  Input,
  OnInit,
  Output,
} from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { CommonModule } from '@angular/common';
import { IliasService } from '../../../core/services/ilias.service';

export type PublishMode = 'assignment' | 'slides' | 'announcement';

@Component({
  selector: 'app-publish-modal',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './publish-modal.component.html',
  styleUrls: ['./publish-modal.component.scss'],
})
export class PublishModalComponent implements OnInit {
  @Input() mode!: PublishMode;
  @Input() courseId!: number;
  @Output() closed = new EventEmitter<boolean>();

  form!: FormGroup;
  loading = false;
  successMessage = '';
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

  private buildForm(): void {
    switch (this.mode) {
      case 'assignment':
        this.form = this.fb.group({
          title: ['', [Validators.required, Validators.minLength(3)]],
          instruction: ['', [Validators.required, Validators.minLength(10)]],
          deadline_date: [''],
          deadline_time: [''],
        });
        break;

      case 'slides':
        this.form = this.fb.group({
          folder_title: ['', [Validators.required, Validators.minLength(3)]],
          description: [''],
        });
        break;

      case 'announcement':
        this.form = this.fb.group({
          title: ['', [Validators.required, Validators.minLength(3)]],
          content: ['', [Validators.required, Validators.minLength(10)]],
          visibility: ['users', Validators.required],
        });
        break;
    }
  }

  get modalTitle(): string {
    switch (this.mode) {
      case 'assignment': return '📝 New Assignment';
      case 'slides': return '📁 Upload Slides';
      case 'announcement': return '📢 New Announcement';
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

    if (this.mode === 'slides' && this.selectedFiles.length === 0) {
      this.errorMessage = 'Please select at least one file to upload.';
      return;
    }

    this.loading = true;
    this.errorMessage = '';
    this.successMessage = '';

    const obs$ = (() => {
      switch (this.mode) {
        case 'assignment':
          return this.iliasService.publishAssignment(
            this.courseId,
            this.form.value,
            this.selectedFile ?? undefined
          );

        case 'slides':
          return this.iliasService.publishSlides(
            this.courseId,
            this.form.value,
            this.selectedFiles
          );

        case 'announcement':
          return this.iliasService.publishAnnouncement(
            this.courseId,
            this.form.value
          );
      }
    })();

    obs$.subscribe({
      next: (result) => {
        this.loading = false;
        this.successMessage = result.message || 'Published successfully!';
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

  close(): void {
    this.closed.emit(!!this.successMessage);
  }

  onOverlayClick(event: MouseEvent): void {
    if ((event.target as HTMLElement).classList.contains('modal-overlay')) {
      this.close();
    }
  }
}
