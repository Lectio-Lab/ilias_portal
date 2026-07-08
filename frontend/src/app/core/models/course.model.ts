export interface Course {
  course_id: number;
  title: string;
  url: string;
  role?: string;
  last_refreshed?: string;
}

export interface CourseItem {
  title: string;
  url: string;
  type: string;
  properties: Record<string, string>;
}

export interface CourseSection {
  section: string;
  items: CourseItem[];
}

export interface CourseContents {
  course_title: string;
  sections: CourseSection[];
}
