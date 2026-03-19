import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import RegisterView from '../RegisterView.vue'

const routes = [{ path: '/', component: { template: '' } }]
const router = createRouter({
  history: createWebHistory(),
  routes,
})

describe('RegisterView.vue', () => {
  it('renders the registration form', () => {
    const wrapper = mount(RegisterView, { global: { plugins: [router] } })
    expect(wrapper.find('h1').text()).toBe('Create an Account')
    expect(wrapper.findAll('input').length).toBe(3)
    expect(wrapper.find('button[type="submit"]').text()).toBe('Create Account')
  })

  it('submits the form and redirects on success', async () => {
    const push = vi.spyOn(router, 'push')
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ success: true }),
      }) as Promise<Response>
    )

    const wrapper = mount(RegisterView, { global: { plugins: [router] } })

    await wrapper.find('input[type="text"]').setValue('Test User')
    await wrapper.findAll('input[type="text"]')[1].setValue('20240002')
    await wrapper.find('input[type="password"]').setValue('password')
    await wrapper.find('form').trigger('submit.prevent')

    expect(global.fetch).toHaveBeenCalledWith('/api/register', expect.any(Object))
    await wrapper.vm.$nextTick()
    expect(push).toHaveBeenCalledWith('/')
  })
})
