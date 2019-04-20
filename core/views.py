from django.shortcuts import render, reverse, redirect
from django.views.generic import ListView, DetailView
from .models import Movie, Person, Vote
from .forms import VoteForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView
from django.core.exceptions import PermissionDenied


class MovieList(ListView):
    model = Movie
    paginate_by = 10


class MovieDetail(DetailView):
    queryset = Movie.objects.all_with_related_persons()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            vote = Vote.objects.get_vote_or_unsaved_blank_vote(
                movie=self.object, user=self.request.user)
            if vote.id:
                vote_form_url = reverse('core:UpdateVote',
                                        kwargs={
                                            'movie_id': vote.movie.id,
                                            'pk': vote.id})
            else:
                vote_form_url = (reverse('core:CreateVote', kwargs={
                                 'movie_id': self.object.id}))
            vote_form = VoteForm(instance=vote)
            context['vote_form'] = vote_form
            context['vote_from_url'] = vote_form_url
        return context


class PersonDetail(DetailView):
    queryset = Person.objects.all_with_prefetch_movies()


class CreateVote(LoginRequiredMixin, CreateView):
    form_class = VoteForm

    def get_initial(self):
        initial = super().get_initial()
        initial['user'] = self.request.user.id
        initial['movie'] = self.kwargs['movie_id']
        return initial


class UpdateVote(LoginRequiredMixin, UpdateView):
    form_class = VoteForm
    queryset = Vote.objects.all()

    def get_object(self, queryset=None):
        vote = super().get_object(queryset)
        user = self.request.user
        if vote.user != user:
            raise PermissionDenied("Cannot change another users vote")
        return vote

    def get_success_url(self):
        movie_id = self.object.movie.id
        return reverse(
            'core:MovieDetail',
            kwargs={'pk': movie_id})

    def render_to_response(self, context, **response_kwargs):
        movie_id = context['object'].id
        movie_detail_url = reverse('core:MovieDetail', kwargs={'pk': movie_id})
        return redirect(to=movie_detail_url)
