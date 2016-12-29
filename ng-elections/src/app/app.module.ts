import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpModule } from '@angular/http';

import { AppComponent } from './app.component';
import {NgbModule} from '@ng-bootstrap/ng-bootstrap';
import { HomeComponent } from './home/home.component';
import {AppRoutingModule} from './app-routing/app-routing.module';
import { VoteComponent } from './vote/vote.component';

@NgModule({
  declarations: [
    AppComponent,
    HomeComponent,
    VoteComponent
  ],
  imports: [
    AppRoutingModule,
    NgbModule.forRoot(),
    BrowserModule,
    FormsModule,
    HttpModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }