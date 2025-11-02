@extends('layout')

@section('title')
    Posts - @parent
@endsection

@section('content')
    <h2>Posts</h2>
    @foreach($posts as $post)
        <article>
            <h3>{{ $post.title }}</h3>
            <p>{{ $post.body }}</p>
        </article>
    @endforeach
@endsection
