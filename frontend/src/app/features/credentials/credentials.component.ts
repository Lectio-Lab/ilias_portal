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
  existingCredentials: IliasCredential | null = null;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService
  ) {
    this.form = this.fb.group({
      ilias_username: [
        '',
        [Validators.pattern(/^$|^zx[a-z0-9]+$/i)],
      ],
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

  onSubmit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading = true;
    this.successMessage = '';
    this.errorMessage = '';

    const { ilias_username } = this.form.value;

    this.authService.saveIliasCredentials(ilias_username || '').subscribe({
      next: (creds) => {
        this.loading = false;
        this.existingCredentials = creds;
        this.successMessage =
          'Optional username hint saved. University passwords are never stored — use Refresh from ILIAS and complete MFA in the browser.';
      },
      error: (err) => {
        this.loading = false;
        if (err.status === 400) {
          this.errorMessage =
            err.error?.ilias_password?.[0] ||
            err.error?.detail ||
            'Invalid request. University passwords cannot be saved.';
        } else if (err.status === 0) {
          this.errorMessage = 'Cannot connect to server.';
        } else {
          this.errorMessage = 'Failed to save. Please try again.';
        }
      },
    });
  }
}
