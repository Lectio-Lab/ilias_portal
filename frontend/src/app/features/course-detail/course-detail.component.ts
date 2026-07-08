import { Component, OnInit } from "@angular/core";
import { ActivatedRoute, Router, RouterLink } from "@angular/router";
import { CommonModule } from "@angular/common";
import { IliasService } from "../../core/services/ilias.service";
import {
  CourseContents,
  CourseItem,
  CourseSection,
} from "../../core/models/course.model";
import {
  PublishModalComponent,
  PublishMode,
} from "./publish-modal/publish-modal.component";
import { TotalItemsPipe } from "../../shared/pipes/total-items.pipe";

@Component({
  selector: "app-course-detail",
  standalone: true,
  imports: [CommonModule, RouterLink, PublishModalComponent, TotalItemsPipe],
  templateUrl: "./course-detail.component.html",
  styleUrls: ["./course-detail.component.scss"],
})
export class CourseDetailComponent implements OnInit {
  courseId!: number;
  contents: CourseContents | null = null;
  loading = true;
  errorMessage = "";

  expandedSections = new Set<number>();

  // Modal state
  showModal = false;
  modalMode: PublishMode = "assignment";

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private iliasService: IliasService,
  ) {}

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get("id");
    if (!idParam || isNaN(Number(idParam))) {
      this.router.navigate(["/courses"]);
      return;
    }

    this.courseId = Number(idParam);
    this.loadContents();
  }

  loadContents(): void {
    this.loading = true;
    this.errorMessage = "";

    this.iliasService.getCourseContents(this.courseId).subscribe({
      next: (data) => {
        this.contents = data;
        this.loading = false;
        // Expand first section by default
        if (data.sections.length > 0) {
          this.expandedSections.add(0);
        }
      },
      error: (err) => {
        this.loading = false;
        if (err.status === 404) {
          this.errorMessage = "Course not found or contents are unavailable.";
        } else if (err.status === 0) {
          this.errorMessage = "Cannot connect to server.";
        } else {
          this.errorMessage =
            err.error?.detail || "Failed to load course contents.";
        }
      },
    });
  }

  toggleSection(index: number): void {
    if (this.expandedSections.has(index)) {
      this.expandedSections.delete(index);
    } else {
      this.expandedSections.add(index);
    }
  }

  isSectionExpanded(index: number): boolean {
    return this.expandedSections.has(index);
  }

  expandAll(): void {
    this.contents?.sections.forEach((_, i) => this.expandedSections.add(i));
  }

  collapseAll(): void {
    this.expandedSections.clear();
  }

  openModal(mode: PublishMode): void {
    this.modalMode = mode;
    this.showModal = true;
  }

  onModalClosed(published: boolean): void {
    this.showModal = false;
    if (published) {
      this.loadContents();
    }
  }

  getItemIcon(type: string): string {
    const t = type.toLowerCase();
    if (t.includes("file") || t.includes("document") || t.includes("pdf"))
      return "fas fa-file-alt";
    if (t.includes("video") || t.includes("media")) return "fas fa-play-circle";
    if (t.includes("assignment") || t.includes("exercise"))
      return "fas fa-tasks";
    if (t.includes("forum") || t.includes("discussion"))
      return "fas fa-comments";
    if (t.includes("folder") || t.includes("group")) return "fas fa-folder";
    if (t.includes("wiki")) return "fas fa-book";
    if (t.includes("survey") || t.includes("test") || t.includes("quiz"))
      return "fas fa-clipboard-check";
    if (t.includes("link") || t.includes("url"))
      return "fas fa-external-link-alt";
    if (t.includes("announcement") || t.includes("news"))
      return "fas fa-bullhorn";
    return "fas fa-cube";
  }

  getItemIconColor(type: string): string {
    const t = type.toLowerCase();
    if (t.includes("file") || t.includes("document") || t.includes("pdf"))
      return "#818cf8";
    if (t.includes("video") || t.includes("media")) return "#f59e0b";
    if (t.includes("assignment") || t.includes("exercise")) return "#34d399";
    if (t.includes("forum") || t.includes("discussion")) return "#06b6d4";
    if (t.includes("folder")) return "#fbbf24";
    if (t.includes("test") || t.includes("quiz")) return "#f87171";
    return "#94a3b8";
  }

  isDownloadable(item: CourseItem): boolean {
    const t = item.type.toLowerCase();
    return (
      t.includes("file") ||
      t.includes("document") ||
      t.includes("pdf") ||
      t.includes("media")
    );
  }

  getDownloadUrl(url: string): string {
    return this.iliasService.getDownloadUrl(url);
  }

  trackBySection(_: number, section: CourseSection): string {
    return section.section;
  }

  trackByItem(_: number, item: CourseItem): string {
    return item.url || item.title;
  }
}
