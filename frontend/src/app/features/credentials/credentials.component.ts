import { Component, OnInit } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';
import { IliasCredential } from '../../core/models/user.model';

@Component({
  selector: 'app-credentials',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './credentials.component.html',
  styleUrls: ['./credentials.component.scss'],
})
export class CredentialsComponent implements OnInit {
  form: FormGroup;
  loading = false;
  loadingCredentials = true;
  successMessage = '';
  errorMessage = '';
  showPassword = false;
  existingCredentials: IliasCredential | null = null;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService
  ) {
    this.form = this.fb.group({
      ilias_username: [
        '',
        [Validators.required, Validators.pattern(/^zx[a-z0-9]+$/i)],
      ],
      ilias_password: ['', [Validators.required, Validators.minLength(6)]],
    });
  }

  ngOnInit(): void {
    this.authService.getIliasCredentials().subscribe({
      next: (creds) => {
        this.existingCredentials = creds;
        if (creds?.ilias_username) {
          this.form.patchValue({ ilias_username: creds.ilias_username });
        }
        this.loadingCredentials = false;
      },
      error: () => {
        this.loadingCredentials = false;
      },
    });
  }

  get usernameCtrl() { return this.form.get('ilias_username')!; }
  get passwordCtrl() { return this.form.get('ilias_password')!; }

  onSubmit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading = true;
    this.successMessage = '';
    this.errorMessage = '';

    const { ilias_username, ilias_password } = this.form.value;

    this.authService.saveIliasCredentials(ilias_username, ilias_password).subscribe({
      next: (creds) => {
        this.loading = false;
        this.existingCredentials = creds;
        this.successMessage = 'ILIAS credentials saved successfully! You can now refresh your courses.';
        this.form.patchValue({ ilias_password: '' });
        this.form.get('ilias_password')?.markAsUntouched();
      },
      error: (err) => {
        this.loading = false;
        if (err.status === 400) {
          this.errorMessage = err.error?.detail || 'Invalid credentials format.';
        } else if (err.status === 0) {
          this.errorMessage = 'Cannot connect to server.';
        } else {
          this.errorMessage = 'Failed to save credentials. Please try again.';
        }
      },
    });
  }
}
