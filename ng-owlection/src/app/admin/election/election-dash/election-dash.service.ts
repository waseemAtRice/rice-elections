import { Injectable } from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {InternalsElection } from '../../../internals/models/internals-election';
import {Observable} from 'rxjs/Observable';

@Injectable()
export class ElectionDashService {

  constructor(
    private http: HttpClient
  ) { }

  get_elections() { }

}

