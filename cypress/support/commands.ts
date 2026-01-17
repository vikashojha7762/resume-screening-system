/// <reference types="cypress" />

declare global {
  namespace Cypress {
    interface Chainable {
      login(email: string, password: string): Chainable<void>;
      logout(): Chainable<void>;
    }
  }
}

Cypress.Commands.add('login', (email: string, password: string) => {
  cy.request({
    method: 'POST',
    url: 'http://localhost:8000/api/v1/auth/login/json',
    body: {
      username: email,
      password: password,
    },
  }).then((response) => {
    window.localStorage.setItem('token', response.body.access_token);
  });
});

Cypress.Commands.add('logout', () => {
  window.localStorage.removeItem('token');
});

export {};

