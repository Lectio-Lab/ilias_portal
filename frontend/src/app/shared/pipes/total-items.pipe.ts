import { Pipe, PipeTransform } from '@angular/core';
import { CourseSection } from '../../core/models/course.model';

@Pipe({
  name: 'totalItems',
  standalone: true,
})
export class TotalItemsPipe implements PipeTransform {
  transform(sections: CourseSection[]): number {
    return sections.reduce((sum, section) => sum + section.items.length, 0);
  }
}
